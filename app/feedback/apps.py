from django.apps import AppConfig

class FeedbackConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "feedback"

    def ready(self):
        """
        Populate default TalentCategories, but only if the database exists.
        """
        import sys
        if "migrate" in sys.argv or "makemigrations" in sys.argv or "test" in sys.argv:
            return  # ✅ Skip running during migrations & tests

        from django.db.utils import OperationalError, ProgrammingError
        from feedback.models import TalentCategory, Talent

        try:
            categories = {
                "Technical Skills": ["Coding", "Data Analysis", "AI Development"],
                "Soft Skills": ["Public Speaking", "Leadership", "Conflict Resolution"],
                "Creativity": ["Graphic Design", "Music Composition", "Photography"],
            }

            for category_name, talents in categories.items():
                category, created = TalentCategory.objects.get_or_create(name=category_name)
                for talent_name in talents:
                    Talent.objects.get_or_create(name=talent_name, category=category)

        except (OperationalError, ProgrammingError):
            # ✅ Skip if database tables do not exist yet
            pass

