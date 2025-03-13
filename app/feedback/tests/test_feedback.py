"""
Tests for creating QR codes for feedback, and giving feedback.
"""

import uuid
import json
from core.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from feedback.models import FeedbackInvitation, PersonalityTrait, TalentCategory, Talent, Feedback

class InvitationTestCase(TestCase):
    """Tests for generating QR Code and sending feedback invitation"""
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='user@example.com', password="password123")

        # Log in the user to get an auth token (if using TokenAuth)
        self.client.force_authenticate(user=self.user)

        # Create an invitation
        self.invitation = FeedbackInvitation.objects.create(
            inviter=self.user,
            invitee_email="invitee@example.com"
        )

    def test_create_invitation(self):
        """
        Ensure a logged-in user can create an invitation.
        """
        data = {"invitee_email": "newuser@example.com"}
        response = self.client.post("/api/feedback/invitations/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("qr_code", response.data)  # Ensure QR code is returned
        self.assertEqual(response.data["invitee_email"], "newuser@example.com")

    def test_qr_code_generation(self):
        """
        Ensure QR code is generated for an invitation.
        """
        response = self.client.get(f"/api/feedback/invitations/{self.invitation.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("qr_code", response.data)  # QR code should be in response

    def test_invitation_acceptance(self):
        """
        Ensure an invited user can accept an invitation.
        """
        response = self.client.post(f"/api/feedback/invite/accept/{self.invitation.id}/")
        self.invitation.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.invitation.used)  # Invitation should be marked as used

    def test_invalid_invitation_id(self):
        """
        Ensure feedback submission fails for an invalid invitation ID.
        """
        fake_id = uuid.uuid4()  # Generate a random UUID
        feedback_data = {
            "name": "Charlie",
            "email": "charlie@example.com",
            "message": "Nice!",
            "rating": 5
        }

        response = self.client.post(f"/api/invitations/{fake_id}/submit_feedback/", feedback_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FeedbackTestCase(TestCase):
    """Tests for valid Feedback."""
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='user@example.com', password="password123")
        self.client.force_authenticate(user=self.user)

        # Create sample categories and talents
        self.personality1 = PersonalityTrait.objects.create(name="Creative")
        self.personality2 = PersonalityTrait.objects.create(name="Analytical")

        self.talent_category1 = TalentCategory.objects.create(name="Technical Skills")
        self.talent_category2 = TalentCategory.objects.create(name="Soft Skills")
        self.empty_talent_category = TalentCategory.objects.create(name="No Talents")

        self.talent1 = Talent.objects.create(name="Coding", category=self.talent_category1)
        self.talent2 = Talent.objects.create(name="Data Analysis", category=self.talent_category1)
        self.talent3 = Talent.objects.create(name="Public Speaking", category=self.talent_category2)
        self.talent4 = Talent.objects.create(name="Leadership", category=self.talent_category2)

        print(f"Created Talent Category ID: {self.talent_category1.id}")  # ✅ Debugging output

        # Create an invitation that has been used
        self.invitation = FeedbackInvitation.objects.create(
            inviter=self.user,
            invitee_email="invitee@example.com",
            used=True  # Ensure invitation is already used for feedback submission
        )

    def test_create_invitation(self):
        """
        Ensure a logged-in user can create an invitation.
        """
        data = {"invitee_email": "newuser@example.com"}
        response = self.client.post("/api/feedback/invitations/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("invitee_email", response.data)
        self.assertEqual(response.data["invitee_email"], "newuser@example.com")

    def test_submit_feedback(self):
        """
        Ensure invited users can submit feedback with valid radar chart values.
        """
        feedback_data = {
            "name": "Alice",
            "email": "alice@example.com",
            "feedback_type": "quick",
            "category_driving": 4,
            "category_exploring": 4,
            "category_understanding": 2,
            "category_communicating": 4,  # Sum = 14
            "personality_traits": [self.personality1.id, self.personality2.id],
            "talents": [self.talent1.id, self.talent2.id]
        }

        response = self.client.post(f"/api/feedback/submit/{self.invitation.id}/", feedback_data)
        # Print API response for debugging
        # print("API Response:", response.status_code, response.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Unexpected Response: {response.data}")

        # Fetch the feedback again
        self.assertTrue(Feedback.objects.filter(invitation=self.invitation).exists(), "Feedback was not created")

        feedback = Feedback.objects.get(invitation=self.invitation)
        self.assertEqual(feedback.personality_traits.count(), 2)
        self.assertEqual(feedback.talents.count(), 2)

    def test_radar_chart_validation(self):
        """
        Ensure radar chart input is validated (sum must be 14).
        """
        invalid_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "feedback_type": "quick",
            "category_driving": 10,
            "category_exploring": 3,
            "category_communicating": 2,
            "category_understanding": 2,  # Sum = 17 (Invalid)
            "personality_categories": [self.personality1.id],
            "talents": [self.talent1.id]
        }

        response = self.client.post(f"/api/feedback/submit/{self.invitation.id}/", invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("The total sum of category values must be exactly 14.", response.data["non_field_errors"])

    def test_duplicate_feedback_submission(self):
        """
        Ensure users cannot submit feedback twice for the same invitation.
        """
        feedback = Feedback.objects.create(
            invitation=self.invitation,
            name="Alice",
            email="alice@example.com",
            category_driving=4,
            category_exploring=4,
            category_understanding=4,
            category_communicating=2
        )
        feedback.personality_traits.add(self.personality1)
        feedback.talents.add(self.talent1)

        duplicate_feedback = {
            "name": "Bob",
            "email": "bob@example.com",
            "category_driving": 4,
            "category_exploring": 4,
            "category_communicating": 4,
            "category_understanding": 4,
            "personality_traits": [self.personality2.id],
            "talents": [self.talent2.id]
        }

        response = self.client.post(f"/api/feedback/submit/{self.invitation.id}/", duplicate_feedback)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Feedback already submitted", response.data["error"])

    def test_list_personality_traits(self):
        """
        Ensure API returns all available personality traits.
        """
        response = self.client.get("/api/feedback/personality_traits/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["name"], "Creative")

    def test_list_talent_categories(self):
        """
        Ensure API returns all available talent categories with talents grouped.
        """
        response = self.client.get("/api/feedback/talent_categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # ✅ Should return 3 categories

        # ✅ Ensure talents are returned properly in "Technical Skills"
        tech_category = next(cat for cat in response.data if cat["name"] == "Technical Skills")
        self.assertEqual(len(tech_category["talents"]), 2)
        self.assertEqual(tech_category["talents"][0]["name"], "Coding")
        self.assertEqual(tech_category["talents"][1]["name"], "Data Analysis")

        # ✅ Ensure talents are returned properly in "Soft Skills"
        soft_category = next(cat for cat in response.data if cat["name"] == "Soft Skills")
        self.assertEqual(len(soft_category["talents"]), 2)
        self.assertEqual(soft_category["talents"][0]["name"], "Public Speaking")
        self.assertEqual(soft_category["talents"][1]["name"], "Leadership")

    def test_invalid_invitation_id(self):
        """
        Ensure feedback submission fails for an invalid invitation ID.
        """
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

    def test_talent_category_with_no_talents(self):
        """
        Ensure a talent category with no talents returns an empty list.
        """
        response = self.client.get("/api/feedback/talent_categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        empty_category = next(cat for cat in response.data if cat["name"] == "No Talents")
        self.assertEqual(empty_category["talents"], [])  # ✅ No talents should be listed

    def test_fetch_individual_talent_category(self):
        """
        Ensure a single talent category returns the correct data.
        """
        print(f"Testing Talent Category ID: {self.talent_category1.id}")  # ✅ Debugging line

        response = self.client.get(f"/api/feedback/talent_categories/{self.talent_category1.id}/")

        print("Test Request URL:", f"/api/feedback/talent_categories/{self.talent_category1.id}/")  # ✅ Debugging
        print("Response Status Code:", response.status_code)  # ✅ Debugging
        print("Response Data:", response.data)  # ✅ Debugging

    #     self.assertEqual(response.status_code, status.HTTP_200_OK)

    # def test_invalid_talent_category_returns_404(self):
    #     """
    #     Ensure requesting a non-existing talent category returns 404.
    #     """
    #     fake_id = uuid.uuid4()
    #     response = self.client.get(f"/api/feedback/talent_categories/{fake_id}/")
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # def test_submit_feedback_with_talents(self):
    #     """
    #     Ensure feedback submission correctly links talents to feedback.
    #     """
    #     feedback_data = {
    #         "name": "Alice",
    #         "email": "alice@example.com",
    #         "feedback_type": "quick",
    #         "category_driving": 4,
    #         "category_exploring": 4,
    #         "category_understanding": 4,
    #         "category_communicating": 4,  # Sum = 16
    #         "personality_traits": [self.personality1.id, self.personality2.id],
    #         "talents": [self.talent1.id, self.talent3.id]  # ✅ Selecting "Coding" & "Public Speaking"
    #     }

    #     response = self.client.post(f"/api/feedback/submit/{self.invitation.id}/", feedback_data)
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Unexpected Response: {response.data}")

    #     # ✅ Ensure feedback was created
    #     self.assertTrue(Feedback.objects.filter(invitation=self.invitation).exists(), "Feedback was not created")

    #     # ✅ Check that talents were linked correctly
    #     feedback = Feedback.objects.get(invitation=self.invitation)
    #     self.assertEqual(feedback.talents.count(), 2)
    #     self.assertTrue(feedback.talents.filter(name="Coding").exists())
    #     self.assertTrue(feedback.talents.filter(name="Public Speaking").exists())

    # def test_submit_feedback_without_talents(self):
    #     """
    #     Ensure feedback submission works even if no talents are selected.
    #     """
    #     feedback_data = {
    #         "name": "Bob",
    #         "email": "bob@example.com",
    #         "feedback_type": "quick",
    #         "category_driving": 4,
    #         "category_exploring": 4,
    #         "category_understanding": 4,
    #         "category_communicating": 4,  # Sum = 16
    #         "personality_traits": [self.personality1.id],
    #         "talents": []  # ✅ No talents selected
    #     }

    #     response = self.client.post(f"/api/feedback/submit/{self.invitation.id}/", feedback_data)
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    #     # ✅ Ensure feedback was created without talents
    #     feedback = Feedback.objects.get(invitation=self.invitation)
    #     self.assertEqual(feedback.talents.count(), 0)  # ✅ Should have no talents linked
