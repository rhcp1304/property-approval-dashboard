import re
import io
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.dateparse import parse_datetime
from pptx import Presentation
from store.models import ApprovedLenskartStore


class Command(BaseCommand):
    help = 'API Fetch + PPT Download + Contextual Extraction (Lookahead Logic)'

    def extract_val(self, label, next_label, text):
        """
        Extracts value only when the specific sequence of labels is found.
        This bypasses 'ghost' or 'template' text by validating the 'neighbor' label.
        """
        if not text:
            return "N/A"

        # This regex looks for: LABEL : VALUE (but only if followed by NEXT_LABEL)
        # The (?={next_label}) is the 'Anchor' that ensures we are in the right table.
        pattern = rf'{label}\s*[:\-]?\s*(.*?)(?={next_label})'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

        if match:
            # Clean up colons and extra whitespace
            return match.group(1).strip().lstrip(':').strip()
        return "N/A"

    def handle(self, *args, **options):
        # --- STEP 1: API CALL ---
        url = "https://retailapis-in.geoiq.ai/bdapp/prod/v1/bd/getAllKissflowProperties"
        headers = {
            'x-api-key': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJtYWlsSWRlbnRpdHkiOiJsZW5za2FydC1hZG1pbkBnZW9pcS5pbyJ9.SbaX7dGyaRz_EVwgdE-cQe7_c0pCnM2OPJD2legV0jU'
        }

        self.stdout.write("Fetching properties...")
        try:
            response = requests.post(url, headers=headers, json={}, timeout=60)
            api_data = response.json().get('data', [])
        except Exception as e:
            self.stderr.write(f"API Failed: {e}")
            return

        for item in api_data:
            prop_id = item.get('property_id')
            ppt_url = item.get('ppt_url')

            store, _ = ApprovedLenskartStore.objects.update_or_create(
                property_id=prop_id,
                defaults={
                    'property_name': item.get('property_name'),
                    'property_address': item.get('property_address'),
                    'latitude': item.get('property_lat'),
                    'longitude': item.get('property_lng'),
                    'ppt_url_raw': ppt_url,
                }
            )

            if ppt_url:
                try:
                    ppt_res = requests.get(ppt_url, timeout=30)
                    if ppt_res.status_code == 200:
                        file_content = ppt_res.content
                        store.ppt_file.save(f"store_{prop_id}.pptx", ContentFile(file_content), save=False)

                        # --- STEP 2: CONTEXTUAL EXTRACTION ---
                        prs = Presentation(io.BytesIO(file_content))
                        if len(prs.slides) > 0:
                            first_slide = prs.slides[0]
                            # Combine all text into one block to preserve the label sequence
                            full_text = ""
                            for shape in first_slide.shapes:
                                if hasattr(shape, "text"):
                                    full_text += shape.text + "\n"

                            # Extract by validating the next expected label in the table
                            store.store_size = self.extract_val("STORE SIZE", "FRONTAGE", full_text)
                            store.frontage = self.extract_val("FRONTAGE", "SIGNAGE WIDTH", full_text)
                            store.signage_width = self.extract_val("SIGNAGE WIDTH", "SIGNAGE HEIGHT", full_text)
                            store.signage_height = self.extract_val("SIGNAGE HEIGHT", "CEILING HEIGHT", full_text)
                            store.ceiling_height = self.extract_val("CEILING HEIGHT", "HEIGHT FROM BEAM BOTTOM",
                                                                    full_text)
                            store.height_from_beam_bottom = self.extract_val("HEIGHT FROM BEAM BOTTOM", "TRADE AREA",
                                                                             full_text)
                            store.trade_area = self.extract_val("TRADE AREA", "Catchment Overview", full_text)

                        # --- STEP 3: FINANCIALS (Scan all slides) ---
                        all_text = ""
                        for slide in prs.slides:
                            for shape in slide.shapes:
                                if hasattr(shape, "text"): all_text += shape.text + " "

                        rev_m = re.search(r'Revenue Projection.*?(\d[\d,.]+)', all_text, re.I)
                        if rev_m: store.geoiq_projected_revenue = rev_m.group(1).replace(',', '')

                        rent_m = re.search(r'Total Rent.*?(\d[\d,.]+)', all_text, re.I)
                        if rent_m: store.proposed_rent = rent_m.group(1).replace(',', '')

                        store.save()
                        self.stdout.write(f"Updated: {prop_id} | Size: {store.store_size}")
                except Exception as e:
                    self.stderr.write(f"Error on {prop_id}: {e}")

        self.stdout.write(self.style.SUCCESS("Process Complete."))