from django.core.management.base import BaseCommand
from django.conf import settings
import os, csv
from scanner.models import ScanHistory
from django.db import IntegrityError

CSV_NAME = os.path.join(settings.BASE_DIR, 'scanner', 'data', 'seed_samples.csv')

class Command(BaseCommand):
    help = "Seed ScanHistory rows from scanner/data/seed_samples.csv (skips duplicates)"

    def handle(self, *args, **options):
        if not os.path.exists(CSV_NAME):
            self.stdout.write(self.style.ERROR("Seed CSV not found at: " + CSV_NAME))
            return

        created = 0
        skipped = 0
        with open(CSV_NAME, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                url = (r.get('url') or r.get('URL') or '').strip()
                label = (r.get('label') or r.get('is_phishing') or r.get('phish') or '').strip()
                prob_raw = r.get('probability') or r.get('prob') or '0'
                try:
                    prob = float(prob_raw)
                except Exception:
                    prob = 0.0
                if not url:
                    skipped += 1
                    continue
                is_phish = str(label).strip().lower() in ('1','true','phishing','yes','phish')
                result_text = "Phishing" if is_phish else "Safe"
                try:
                    obj, created_flag = ScanHistory.objects.get_or_create(
                        url=url,
                        defaults={
                            'result': result_text,
                            'probability': prob,
                            'features_json': {},
                            'user': None,
                        }
                    )
                    if created_flag:
                        created += 1
                    else:
                        skipped += 1
                except IntegrityError as ie:
                    # duplicate unique key or other DB constraint
                    skipped += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error creating {url}: {e}"))
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(f"Seed finished. created={created}, skipped={skipped}"))
