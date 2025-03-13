from django.apps import AppConfig

class FeedbackConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "feedback"

    def ready(self):
        """
        Populate default TalentCategories, PersonalityQualities but only if the database exists.
        """
        import sys
        if "migrate" in sys.argv or "makemigrations" in sys.argv or "test" in sys.argv:
            return  # ✅ Skip running during migrations & tests

        from django.db.utils import OperationalError, ProgrammingError
        from feedback.models import TalentCategory, Talent, Quality, PersonalityTrait

        try:
            categories = {
                "Technical Skills": ["Coding", "Data Analysis", "AI Development"],
                "Soft Skills": ["Public Speaking", "Leadership", "Conflict Resolution"],
                "Creativity": ["Graphic Design", "Music Composition", "Photography"],
            }
            # ✅ Predefined qualities with their personality traits
            qualities = {
                "Resilience": ["Perseverance", "Emotional Stability", "Optimism"],
                "Empathy": ["Compassion", "Active Listening", "Understanding Others"],
                "Leadership": ["Decision Making", "Confidence", "Inspiration"],
                "Creativity": ["Innovation", "Artistic Thinking", "Problem Solving"]
            }

            for category_name, talents in categories.items():
                category, created = TalentCategory.objects.get_or_create(name=category_name)
                for talent_name in talents:
                    Talent.objects.get_or_create(name=talent_name, category=category)

             # ✅ Step 2: Create Qualities first
            quality_mapping = {}
            for quality_name in qualities.keys():
                quality, _ = Quality.objects.get_or_create(name=quality_name)
                quality_mapping[quality_name] = quality  # Store for later use

            # ✅ Step 3: Create PersonalityTraits only after Qualities exist
            for quality_name, traits in qualities.items():
                quality = quality_mapping[quality_name]
                for trait_name in traits:
                    PersonalityTrait.objects.get_or_create(name=trait_name, quality=quality)

        except (OperationalError, ProgrammingError):
            # ✅ Skip if database tables do not exist yet
            pass

