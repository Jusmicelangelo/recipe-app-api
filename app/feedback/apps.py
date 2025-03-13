from django.apps import AppConfig
from django.db.utils import IntegrityError


class FeedbackConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feedback'

    def ready(self):
        from feedback.models import TalentCategory, Talent

        # ✅ Predefined talent categories
        categories = {
            "Technical Skills": ["Coding", "Data Analysis", "AI Development"],
            "Soft Skills": ["Public Speaking", "Leadership", "Conflict Resolution"],
            "Creativity": ["Graphic Design", "Music Composition", "Photography"],
        }

        for category_name, talents in categories.items():
            category, created = TalentCategory.objects.get_or_create(name=category_name)

            for talent_name in talents:
                try:
                    Talent.objects.get_or_create(name=talent_name, category=category)
                except IntegrityError:
                    pass  # Talent already exists

