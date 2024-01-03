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
from django.urls import reverse
from .forms import UpdateUserForm  
import unittest
from unittest.mock import Mock, patch
from unittest.mock import patch, MagicMock





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

        key_strings = ['Total Number of Applications:', 'Total Approved Applications:', 'Total Rejected Applications:', 'Loan Application Statistics']
        for key_string in key_strings:
            with self.subTest(key_string=key_string):
                self.assertContains(response, key_string)

        features = ['Age', 'Income', 'LoanAmount', 'CreditScore', 'MonthsEmployed', 'LoanTerm', 'DTIRatio']
        for feature in features:
            with self.subTest(feature=feature):
                self.assertContains(response, f'value="{feature}" onclick="showTable(\'{feature}\')"')

        for feature in features:
            with self.subTest(feature=feature):
                self.assertContains(response, f'id="{feature}Table" style="display:none;"')

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

        
        response = self.client.post(reverse('register'), data=user_data, follow=True)

        
        print(response.content.decode('utf-8'))

        
        user_exists = CustomUser.objects.filter(username='testuser').exists()
        print(f"User exists in the database: {user_exists}")

        
        print("Session data:")
        print(self.client.session)

        print(f"Response status code: {response.status_code}")

        print(f"User authenticated: {response.context['user'].is_authenticated}")

        if response.status_code == 302:

            print(f"Redirect URL: {response.url}")

            self.assertRedirects(response, reverse('login'), status_code=302)
        else:
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
        if not get_user_model().objects.filter(username='testuser').exists():
            get_user_model().objects.create_user(username='testuser', password='testpassword')

        invalid_login_data = {
            'username': 'testuser',
            'password': 'wrongpassword',
        }

        response = self.client.post(reverse('login'), data=invalid_login_data, follow=True)
        self.assertFalse(response.context['user'].is_authenticated)


        
    def test_login_view_inactive_user(self):
        self.user.is_active = False
        self.user.save()

        inactive_user_data = {
            'username': 'testuser',
            'password': 'testpassword',
        }

        response = self.client.post(reverse('login'), data=inactive_user_data, follow=True)

        self.assertFalse(response.context['user'].is_authenticated)


    def test_login_view_form_validation_error(self):
        response = self.client.post(reverse('login'), data={}, follow=True)

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
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpassword'
        )
        self.image_path = 'path/to/test_image.jpg'
        self.user.image = SimpleUploadedFile('test_image.jpg', b'content', content_type='image/jpeg')
        self.user.save()

    def test_delete_image(self):
        self.client.force_login(self.user)

        initial_image_path = os.path.join('path/to', str(self.user.image))

        response = self.client.get(reverse('delete_image'))

        self.assertEqual(response.status_code, 302)

        self.user.refresh_from_db()

        self.assertEqual(self.user.image, '')

        self.assertFalse(os.path.exists(initial_image_path))

    def tearDown(self):
        self.user.delete()



#class ChatAssistanceTest(TestCase):
   # def setUp(self):
       # self.client = Client()

   # @patch('loanApp.views.ask_openai') 
   # def test_chat_assistance_view(self, mock_ask_openai):

     #   mock_ask_openai.return_value = "Mocked response"
      #  message = "I have a question."

      #  response = self.client.post(reverse('chat_assistance'), {'message': message}, follow=True)

     #   self.assertEqual(response.status_code, 200)
     #   self.assertJSONEqual(response.content, {'message': message, 'response': 'Mocked response'})
     #   mock_ask_openai.assert_called_once_with(message)

    def test_ask_openai_function(self):

        message = "I have a question."

        response = ask_openai(message)

        self.assertIsInstance(response, str)
        self.assertNotEqual(response, "Sorry, I couldn't understand that. This is a different response.")



class TestAskOpenAI(unittest.TestCase):

    @patch("loanApp.views.client.completions.create")
    def test_ask_openai_success(self, mock_create):
        mock_create.return_value.choices[0].text.strip.return_value = "Mocked response"

        message = "Can I get information about loan approval?"
        result = ask_openai(message)

        mock_create.assert_called_once_with(
            model="gpt-3.5-turbo-instruct",
            prompt=f'your role is a chatbot assistance in a website that help with loan approval questions called AILoan and the customer question to you is "{message}"',
            max_tokens=150,
            temperature=0.7
        )

        self.assertEqual(result, "Mocked response")

    @patch("loanApp.views.client.completions.create")
    def test_ask_openai_exception(self, mock_create):
        mock_create.side_effect = Exception("Mocked error")

        message = "Can I get information about loan approval?"
        result = ask_openai(message)

        mock_create.assert_called_once_with(
            model="gpt-3.5-turbo-instruct",
            prompt=f'your role is a chatbot assistance in a website that help with loan approval questions called AILoan and the customer question to you is "{message}"',
            max_tokens=150,
            temperature=0.7
        )

        self.assertEqual(result, "Sorry, I couldn't understand that.")

if __name__ == '__main__':
    unittest.main()

class PerformanceViewTest(TestCase):

    @patch("loanApp.views.get_available_models")
    @patch("loanApp.views.select_model")
    def test_performance_view(self, mock_select_model, mock_get_available_models):
        
        mock_select_model.return_value = MagicMock()  
        mock_get_available_models.return_value = ['Model1', 'Model2']

        client = Client()

        response = client.get(reverse('performance'))

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'admin/performance.html')

