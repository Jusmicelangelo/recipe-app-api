import uuid
import json
from core.models import User
from django.test import TestCase
from rest_framework.test import APIClient  # ✅ Ensure APIClient is imported
from django.urls import reverse
from rest_framework import status
from feedback.models import (
    FeedbackInvitation, PersonalityTrait, TalentCategory, Talent, Feedback, Quality
)


class InvitationTestCase(TestCase):
    """Tests for generating QR Code and sending feedback invitation"""

    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = User.objects.create_user(email='user@example.com', password="password123")

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.invitation = FeedbackInvitation.objects.create(inviter=self.user, invitee_email="invitee@example.com")

    def test_create_invitation(self):
        """Ensure a logged-in user can create an invitation."""
        data = {"invitee_email": "newuser@example.com"}
        response = self.client.post("/api/feedback/invitations/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("qr_code", response.data)

    def test_create_invitation_invalid_email(self):
        """Ensure invitation creation fails for invalid emails."""
        data = {"invitee_email": "invalid-email"}
        response = self.client.post("/api/feedback/invitations/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # def test_duplicate_invitation(self):
    #     """Ensure the same invitee cannot be invited twice."""
    #     data = {"invitee_email": "invitee@example.com"}
    #     response1 = self.client.post("/api/feedback/invitations/", data)
    #     self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

    #     response2 = self.client.post("/api/feedback/invitations/", data)
    #     print("📌 Duplicate Invite Response:", response2.status_code, response2.data)  # Debugging
    #     self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)  # ✅ Should fail

    def test_invitation_acceptance(self):
        """Ensure an invited user can accept an invitation."""
        response = self.client.post(f"/api/feedback/invite/accept/{self.invitation.id}/")
        self.invitation.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.invitation.used)

    def test_invalid_invitation_id(self):
        """Ensure feedback submission fails for an invalid invitation ID."""
        fake_id = uuid.uuid4()
        feedback_data = {"name": "Charlie", "email": "charlie@example.com", "message": "Nice!", "rating": 5}
        response = self.client.post(f"/api/invitations/{fake_id}/submit_feedback/", feedback_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FeedbackTestCase(TestCase):
    """Tests for submitting feedback."""

    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.user = User.objects.create_user(email='user@example.com', password="password123")

        # ✅ Create an unused invitation
        cls.invitation = FeedbackInvitation.objects.create(
            inviter=cls.user,
            invitee_email="invitee@example.com",
            used=False
        )

        # ✅ Create sample data
        cls.quality_creativity = Quality.objects.create(name="Creativity")
        cls.personality1 = PersonalityTrait.objects.create(name="Creative", quality=cls.quality_creativity)
        cls.talent_category1 = TalentCategory.objects.create(name="Technical Skills")
        cls.talent1 = Talent.objects.create(name="Coding", category=cls.talent_category1)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # ✅ Accept the invitation before submitting feedback
        accept_url = reverse("accept-invitation", args=[self.invitation.id])
        response = self.client.post(accept_url)
        self.invitation.refresh_from_db()

        print("📌 Invitation Accept Response:", response.status_code)
        print("📌 Invitation Used Status:", self.invitation.used)  # ✅ Debugging

        assert self.invitation.used is True, "❌ Invitation was NOT accepted!"

    def test_submit_feedback_valid(self):
        """Ensure invited users can submit valid feedback."""
        feedback_data = {
            "name": "Alice",
            "email": "alice@example.com",
            "feedback_type": "quick",
            "category_driving": 4,
            "category_exploring": 4,
            "category_understanding": 2,
            "category_communicating": 4,
            "personality_traits": [self.personality1.id],
            "talents": [self.talent1.id]
        }

        # ✅ Submit Feedback
        url = reverse("submit-feedback", args=[self.invitation.id])
        print("📌 Generated API URL:", url)  # Debugging

        response = self.client.post(url, feedback_data, format="json")
        print("📌 Response Status:", response.status_code)  # Debugging
        print("📌 Response Data:", response.data)  # Debugging

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_submit_feedback_without_talents(self):
        """Ensure feedback submission works even if no talents are selected."""
        feedback_data = {
            "name": "Bob",
            "email": "bob@example.com",
            "feedback_type": "quick",
            "category_driving": 4,
            "category_exploring": 4,
            "category_understanding": 2,
            "category_communicating": 4,
            "personality_traits": [self.personality1.id],
            "talents": []
        }

        # ✅ Submit Feedback
        url = reverse("submit-feedback", args=[self.invitation.id])
        print("📌 Generated API URL:", url)  # Debugging

        response = self.client.post(url, feedback_data, format="json")
        print("📌 Response Status:", response.status_code)  # Debugging
        print("📌 Response Data:", response.data)  # Debugging

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_submit_feedback_invalid_invite(self):
        """Ensure feedback submission fails with an invalid invitation ID."""
        fake_id = uuid.uuid4()
        feedback_data = {
            "name": "Charlie",
            "email": "charlie@example.com",
            "category_driving": 4,
            "category_exploring": 4,
            "category_understanding": 4,
            "category_communicating": 4,
            "personality_traits": [self.personality1.id],
            "talents": [self.talent1.id]
        }
        response = self.client.post(f"/api/feedback/submit/{fake_id}/", feedback_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_talent_categories(self):
        """Ensure API returns all available talent categories with talents grouped."""
        response = self.client.get("/api/feedback/talent_categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Technical Skills")
        self.assertEqual(response.data[0]["talents"][0]["name"], "Coding")

    def test_invalid_talent_category_returns_404(self):
        """Ensure requesting a non-existing talent category returns 404."""
        fake_id = "555"
        response = self.client.get(f"/api/feedback/talent_categories/{fake_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)