from django.test import TestCase
from django.urls import reverse
from loanApp.views import home  
from django.urls import reverse
from loanApp.models import CustomUser
from loanApp.forms import SignUpForm 
from django.test import Client
from loanApp.models import LoanApplicant 
import plotly.express as px
import joblib
import pandas as pd
from unittest.mock import patch
from django.contrib.auth import get_user_model
from .forms import LoginForm
from django.contrib.auth import logout
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from .views import ask_openai



class HomeViewTest(TestCase):
    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

class ReportsViewTest(TestCase):
    def setUp(self):
        LoanApplicant.objects.create(
            Age=25,
            Income=50000,
            LoanAmount=100000,
            CreditScore=700,
            MonthsEmployed=24,
            LoanTerm=36,
            DTIRatio=0.3,
            Default=None
        )

        LoanApplicant.objects.create(
            Age=30,
            Income=60000,
            LoanAmount=120000,
            CreditScore=750,
            MonthsEmployed=60,
            LoanTerm=48,
            DTIRatio=0.25,
            Default=None
        )

    def test_reports_view(self):
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)

        # Check for the presence of key strings in the response
        key_strings = ['Total Number of Applications:', 'Total Approved Applications:', 'Total Rejected Applications:', 'Loan Application Statistics']
        for key_string in key_strings:
            with self.subTest(key_string=key_string):
                self.assertContains(response, key_string)

        # Check for the presence of the radio buttons in the response
        features = ['Age', 'Income', 'LoanAmount', 'CreditScore', 'MonthsEmployed', 'LoanTerm', 'DTIRatio']
        for feature in features:
            with self.subTest(feature=feature):
                self.assertContains(response, f'value="{feature}" onclick="showTable(\'{feature}\')"')

        # Check for the presence of the hidden tables in the response
        for feature in features:
            with self.subTest(feature=feature):
                self.assertContains(response, f'id="{feature}Table" style="display:none;"')

        # Check for the presence of the Plotly chart in the response
        self.assertContains(response, 'Plotly.newPlot')


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register_view_success(self):
        # Define test data for the form
        user_data = {
            'username': 'testuser',
            'password1': 'testpassword123',
            'password2': 'testpassword123',
        }

        # Create a POST request to the register view with the test data
        response = self.client.post(reverse('register'), data=user_data, follow=True)

        # Print the response content for debugging purposes
        print(response.content.decode('utf-8'))

        # Check that the user was created in the database
        user_exists = CustomUser.objects.filter(username='testuser').exists()
        print(f"User exists in the database: {user_exists}")

        # Print the session data for additional debugging
        print("Session data:")
        print(self.client.session)

        # Check the response status code
        print(f"Response status code: {response.status_code}")

        # Check if the user is logged in
        print(f"User authenticated: {response.context['user'].is_authenticated}")

        # If there's a specific URL pattern you're expecting the redirect to, you can check that
        if response.status_code == 302:
            # Redirect URL is only available if the status code is 302
            print(f"Redirect URL: {response.url}")

            # Assuming successful registration, check for a redirect (status code 302)
            self.assertRedirects(response, reverse('login'), status_code=302)
        else:
            # Handle the case where the status code is not 302
            print("No redirect URL available for non-302 status code")




class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = self.create_user(username='testuser', password='testpassword', is_admin=False)

    def create_user(self, **kwargs):
        return get_user_model().objects.create_user(**kwargs)

   # def test_login_view_valid_credentials(self):
        # Define test data for the form
       # login_data = {
           # 'username': 'testuser',
           # 'password': 'testpassword',
       # }

        # Create a POST request to the login view with the test data
       # response = self.client.post(reverse('login'), data=login_data, follow=True)

    
        # Check that the login was successful and the user is redirected to 'create_applicant'
        #self.assertRedirects(response, reverse('create_applicant'))
        


    def test_login_view_invalid_credentials(self):
        # Ensure the user exists; if not, create it
        if not get_user_model().objects.filter(username='testuser').exists():
            get_user_model().objects.create_user(username='testuser', password='testpassword')

        # Define test data for the form with invalid credentials
        invalid_login_data = {
            'username': 'testuser',
            'password': 'wrongpassword',
        }

        # Create a POST request to the login view with invalid credentials
        response = self.client.post(reverse('login'), data=invalid_login_data, follow=True)

        # Check that the user is not authenticated
        self.assertFalse(response.context['user'].is_authenticated)


        
    def test_login_view_inactive_user(self):
        # Deactivate the test user
        self.user.is_active = False
        self.user.save()

        # Define test data for the form with deactivated user credentials
        inactive_user_data = {
            'username': 'testuser',
            'password': 'testpassword',
        }

        # Create a POST request to the login view with deactivated user credentials
        response = self.client.post(reverse('login'), data=inactive_user_data, follow=True)

        # Check that the user is not authenticated
        self.assertFalse(response.context['user'].is_authenticated)


    def test_login_view_form_validation_error(self):
        # Create a POST request to the login view with missing credentials
        response = self.client.post(reverse('login'), data={}, follow=True)

        # Check that the user is not authenticated
        self.assertFalse(response.context['user'].is_authenticated)



    def test_logout_user(self):
     user, created = CustomUser.objects.get_or_create(
        username='testuser',
        defaults={'password': make_password('testpassword')}
    )
     self.client.force_login(user)

     response = self.client.get(reverse('logout'))

     self.assertEqual(response.status_code, 302)
     self.assertRedirects(response, reverse('welcome'))

    # Check for the success message in the response
     messages = response.context and response.context.get('messages')
     if messages is not None:
        messages = [m.message for m in messages]
        self.assertIn("You are logged out.", messages)


class DeleteImageViewTest(TestCase):
    def setUp(self):
        # Create a user and assign an image to the user's profile
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.image_path = 'path/to/test_image.jpg'
        self.user.image = SimpleUploadedFile('test_image.jpg', b'content', content_type='image/jpeg')
        self.user.save()

    def test_delete_image(self):
        # Log in the user
        self.client.force_login(self.user)

        # Get the initial image path
        initial_image_path = os.path.join('path/to', str(self.user.image))

        # Make a GET request to the delete_image view
        response = self.client.get(reverse('delete_image'))

        # Assert that the response is a redirect
        self.assertEqual(response.status_code, 302)

        # Refresh the user instance from the database
        self.user.refresh_from_db()

        # Assert that the user's image field is now empty
        self.assertEqual(self.user.image, '')

        # Assert that the image file has been deleted
        self.assertFalse(os.path.exists(initial_image_path))

    def tearDown(self):
        self.user.delete()



class ChatAssistanceTest(TestCase):
    def setUp(self):
        self.client = Client()

    @patch('loanApp.views.ask_openai')  # Mock the ask_openai function
    def test_chat_assistance_view(self, mock_ask_openai):

        mock_ask_openai.return_value = "Mocked response"
        message = "I have a question."

        response = self.client.post('/chat-assistance/', {'message': message})

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'message': message, 'response': 'Mocked response'})
        mock_ask_openai.assert_called_once_with(message)

    def test_ask_openai_function(self):

        message = "I have a question."

        response = ask_openai(message)

        self.assertIsInstance(response, str)
        self.assertNotEqual(response, "Sorry, I couldn't understand that. This is a different response.")


