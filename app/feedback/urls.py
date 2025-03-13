"""
URL mappings for the feedback app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (FeedbackInvitationViewSet, accept_invitation,
                    submit_feedback, list_personality_traits,
                    list_talent_categories, get_talent_category)

router = DefaultRouter()
router.register(r'invitations', FeedbackInvitationViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("invite/accept/<uuid:invite_id>/", accept_invitation, name="accept-invitation"),
    path("submit/<uuid:invite_id>/", submit_feedback, name="submit-feedback"),
    path("personality_traits/", list_personality_traits, name="list-personality-traits"),
    path("talent_categories/", list_talent_categories, name="list-talent-categories"),
    path("talent_categories/<uuid:category_id>/", get_talent_category, name="get-talent-category"),
]