from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .forms import *
from .models import *
from .utils import *
import plotly.express as px
from plotly.offline import plot
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, confusion_matrix
import numpy as np
import os
from openai import OpenAI
from allauth.account.views import PasswordResetView as AllauthPasswordResetView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
import shap

client = OpenAI(api_key='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')

## User methods

def home(request):
    return render(request, 'home.html')

def loan_history(request):
    return render(request, 'user/loan-history.html')

def reset_password(request):
    return render(request, 'user/reset-password.html')

#Contributor: Cynthia
def aboutUs(request):
    return render(request, 'user/aboutUs.html')


# contributor: Kanokwan
# Creating a new user in the system, with different role
def register(request):
    msg = None
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            msg = 'user created'
            return redirect('login')
        else:
            msg = 'form is not valid'
    else:
        form = SignUpForm()
    return render(request,'register.html', {'form': form, 'msg': msg})

def logout_user(request):
    logout(request)
    messages.success(request, ("You are logged out."))
    return redirect('welcome')

def welcome(request):
    # Create a login form instance with submitted data  
    # Contributer : Nazli, Kanokawan, Akuien
    form = LoginForm(request.POST or None)
    msg = None

    if request.method == 'POST':
        # Check if the form is valid
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
        # Check if authentication was successful
            if user is not None:
                 # Check if the user account is active
                if user.is_active:
                    login(request, user)
                    messages.success(request, 'Login successful')
        # Redirect users based on their roles
                    if user.is_admin:
                        return redirect('predictions')
                    elif user.is_customer:
                        return redirect('create_applicant')
                    else:
                        msg = 'Invalid user role'
                else:
                    msg = 'User is not active'
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating form'

    # Render the home template with the login form and message
    return render(request, "home.html", {
        "form": form, "msg": msg
    })


def user_dashboard(request):
    if request.user.is_authenticated:
        user = request.user

        email = request.user.email
        username = request.user.username
        name = request.user.first_name + " " + request.user.last_name
        
        return render(request, "user/user-dashboard.html", {
            "name": name, 
            "email": email,
            "usr": username,
        })
    else:
        return render(request, 'anonymousProfile.html')


#Contribution: Cynthia
@login_required
def create_applicant(request):
    context = {'messages': []}
    # Check if the request method is POST
    if request.method == 'POST':
        form = LoanForm(request.POST)
    # Check if the form is valid and extract cleaned data from the form
        if form.is_valid():
            Age = form.cleaned_data['Age']
            Income_SEK = form.cleaned_data['Income']
            LoanAmount_SEK = form.cleaned_data['LoanAmount']
            CreditScore = form.cleaned_data['CreditScore']
            MonthsEmployed = form.cleaned_data['MonthsEmployed']
            LoanTerm = form.cleaned_data['LoanTerm']
            DTIRatio = form.cleaned_data['DTIRatio']
            
            # Manual exchange rate for converting SEK to USD
            manual_exchange_rate = 10
            Income_USD = Income_SEK / manual_exchange_rate
            LoanAmount_USD = LoanAmount_SEK / manual_exchange_rate
           
            # Load the machine learning model and make predictions
            model_path = 'MLmodels/model_V3.joblib'
            model = load_model(model_path)
            prediction = model.predict([[Age, Income_USD, LoanAmount_USD, CreditScore, MonthsEmployed, LoanTerm, DTIRatio]])
            print("Prediction Result:", prediction[0])


            # Save to NewLoanApplicant model with status 'pending' and logged-in user
            new_loan_applicant = NewLoanApplicant.objects.create(
                Age=Age,
                Income=Income_USD,
                LoanAmount=LoanAmount_USD,
                CreditScore=CreditScore,
                MonthsEmployed=MonthsEmployed,
                LoanTerm=LoanTerm,
                DTIRatio=DTIRatio,
                Default=prediction[0],
                status='pending',
                user=request.user,
            )
            # Explainable AI
            input_data = np.array([[Age, Income_USD, LoanAmount_USD, CreditScore, MonthsEmployed, LoanTerm, DTIRatio]])
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(input_data)

            if shap_values and isinstance(shap_values, list):
                
                flat_shap_values = flat_shap_values = [item for sublist in shap_values for item in sublist]
                context['shap_values'] = flat_shap_values

                context['Age'] = Age
                context['Income_USD'] = Income_USD
                context['LoanAmount_USD'] = LoanAmount_USD
                context['CreditScore'] = CreditScore
                context['MonthsEmployed'] = MonthsEmployed
                context['LoanTerm'] = LoanTerm
                context['DTIRatio'] = DTIRatio

            # Save input data and prediction to the database
            save_to_database(
                [{
                    'Age': Age,
                    'Income': Income_USD,
                    'LoanAmount': LoanAmount_USD,
                    'CreditScore': CreditScore,
                    'MonthsEmployed': MonthsEmployed,
                    'LoanTerm': LoanTerm,
                    'DTIRatio': DTIRatio,
                }],
                [prediction[0]],
            )
            #context for displaying prediction results
            context['prediction_data'] = {
                'headers': ['Age', 'Income', 'LoanAmount', 'CreditScore', 'MonthsEmployed', 'LoanTerm', 'DTIRatio'],
                'records': [({
                    'Age': Age,
                    'Income': Income_USD,
                    'LoanAmount': LoanAmount_USD,
                    'CreditScore': CreditScore,
                    'MonthsEmployed': MonthsEmployed,
                    'LoanTerm': LoanTerm,
                    'DTIRatio': DTIRatio,
                }, prediction[0])],
            }
            context['application_result'] = "Congratulations, you qualify for a loan!" if prediction[0] == 0 else "Sorry, your application has been rejected."
    else:
        form = LoanForm()
        # Set placeholders for form fields
        form.fields['Age'].widget.attrs['placeholder'] = 'Enter your age'
        form.fields['Income'].widget.attrs['placeholder'] = 'Enter your annual salary in SEK'
        form.fields['LoanAmount'].widget.attrs['placeholder'] = 'Enter your desired loan amount in SEK'
        form.fields['CreditScore'].widget.attrs['placeholder'] = 'Enter your credit score'
        form.fields['MonthsEmployed'].widget.attrs['placeholder'] = 'Enter your total months of employment'
        form.fields['LoanTerm'].widget.attrs['placeholder'] = 'Enter the months to repay'
        form.fields['DTIRatio'].widget.attrs['placeholder'] = 'Enter your debt to income ratio'
    context['form'] = form
    return render(request, 'user/create-applicant.html', context)


@login_required
def view_profile(request):
     if request.user.is_authenticated:
        email = request.user.email
        username = request.user.username
        user = request.user
        hasPfp = user.image != ""

        if request.method == "POST":
            form = UpdateUserForm(request.POST, request.FILES)

            if form.is_valid():
                if user.image != form.cleaned_data["image"] and user.image != "":
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    imagePath = os.path.join(current_dir, '..', 'images', str(user.image))
                    os.remove(imagePath)

                user.first_name = form.cleaned_data["fname"]
                user.last_name = form.cleaned_data["lname"]
                user.username = form.cleaned_data["uname"]
                user.email = form.cleaned_data["email"]
                user.image = form.cleaned_data["image"]
                
                user.save()
                return redirect(view_profile)

        else:
            fname = " "
            lname = " "

            print(user.first_name == "")

            if user.first_name != "":
                fname = user.first_name,
            
            if user.last_name != "":
                fname = user.last_name,

            form = UpdateUserForm(initial={
                "fname": fname,
                "lname": lname,
                "uname": user.username,
                "email": user.email,
                "image": user.image,
            })

        return render(request, "user/profile.html", {
            "id": id, 
            "user": user.username,
            "fname": user.first_name,
            "lname": user.last_name,
            "email": user.email,
            "form": form,
            "image": user.image,
            "hasPfp": hasPfp,
        })
     else:
        return render(request, 'anonymousProfile.html')

@login_required
def delete_image(request):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        imagePath = os.path.join(current_dir, '..', 'images', str(request.user.image))
        os.remove(imagePath)
        request.user.image = ""
        request.user.save()

    except FileNotFoundError:
        print(FileNotFoundError)
    return redirect(view_profile)

@login_required
def remove_user(request):
    if request.method == "GET":
        user = request.user
        user.delete()
        redirect("home")     
    return render(request, "user/remove-user.html")

def profile(request, id):
    try:
        user = CustomUser.objects.get(id=id)    
        position = ""

        if user.is_staff:
            position = "Staff"
        else:
            position = "User"    

        return render(request, "profile.html", {
                "id": id,
                "found": True,
                "fname": user.first_name,
                "lname": user.last_name,
                "usrnm": user.username,
                "email": user.email,
                "position": position,
            })
    except:
        return render(request, "profile.html", {"found": False, "msg": f"User id {id} not found"})
    
login_required
def update(request):
    if request.user.is_authenticated:
        user = request.user
        if request.method == "POST":
            form = UpdateUserForm(request.POST)

            if form.is_valid():
                user.first_name = form.cleaned_data["fname"]
                user.last_name = form.cleaned_data["lname"]
                user.email = form.cleaned_data["email"]
                user.save()
                return redirect('home')
        else:
            form = UpdateUserForm(initial={
                "fname": user.first_name,
                "lname": user.last_name,
                "email": user.email,
            })
        return render(request, "updateUser.html", {
            "found": False,
            "id": id, 
            "user": user.username,
            "fname": user.first_name,
            "lname": user.last_name,
            "email": user.email,
            "form": form,
        })
    else:
        return render(request, "anonymousProfile.html", {"found": False, "msg": f"User id {id} not found"})



def login_view(request): #contributer: Nazli, Kanokwan, Akuien
    form = LoginForm(request.POST or None)
    msg = None

    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
        # Check if authentication was successful
            if user is not None:
                # Check if the user account is active
                if user.is_active:
                    login(request, user)
                    messages.success(request, 'Login successful')
                    # Redirect users based on their roles
                    if user.is_admin:
                        return redirect('predictions')
                    elif user.is_customer:
                        return redirect('create_applicant')
                    else:
                        msg = 'Invalid user role'
                else:
                    msg = 'User is not active'
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating form'
# Render the home template with the login form and message
    return render(request, 'login.html', {'form': form,'msg': msg})

@login_required
def profile(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        # User is authenticated, you can access the email attribute
        email = request.user.email
        return render(request, 'profile.html', {'email': email})
    else:
        # User is not authenticated (anonymous), handle it accordingly
        return render(request, 'anonymousProfile.html')

# contributor: Kanokwan
# Handle chat assistance role in the system, using openAI api
def ask_openai(message):
    try:
        customPrompt = f'your role is a chatbot assistance in a website that help with loan approval questions called AILoan and the customer question to you is "{message}"'
        response = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=customPrompt,
        max_tokens=150,  
        temperature=0.7
    )
        answer = response.choices[0].text.strip()
        return answer
    except Exception as e:
        print(f"Error in ask_openai: {e}")
        return "Sorry, I couldn't understand that."
    
@login_required
def chat_assistance(request):
    if request.method == 'POST':
        message = request.POST.get('message')
        print('Received message:', message)
        response = ask_openai(message)
        print('Sending response:', response)
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'user/chat-assistance.html')


### Admin functions 

#Contributor: Cynthia
@login_required
def information(request):
    context = {'messages': []}
    pending = NewLoanApplicant.objects.filter(status='pending')
    context['pending_count'] = pending.count()
    return render(request, 'admin/information.html', context)


# contributor: kanokwan
# display all the newly made application to the admin dashboard  
@login_required
def applicants(request):
    context = {'messages': []}
    if request.user.is_authenticated:
        applicants = NewLoanApplicant.objects.all()
        pending = NewLoanApplicant.objects.filter(status='pending')
        context['pending_count'] = pending.count()

        return render(request, 'admin/applicants.html', {
            "applicants": applicants,
            "pending_count": context['pending_count'],
        })

    return redirect(login)

# contributor: Kanokwan
# update the reviewing status of the each individual application, working together with the notification
def update_status(request):
    if request.method == 'POST':
        loan_id = request.POST.get('loan_id')
        new_status = request.POST.get('new_status')

        try:
            applicant = NewLoanApplicant.objects.get(LoanID=loan_id)
            applicant.status = new_status
            applicant.save()
            messages.success(request, f'Status updated successfully for Loan ID {loan_id}.')
        except NewLoanApplicant.DoesNotExist:
            messages.error(request, f'Loan ID {loan_id} not found.')

    return redirect('applicants')

#Contribution: Cynthia
#perfom predictions on an uploaded CSV file and the resluts
#can be viewd in a table or as a pie chart
def predictions(request):
    context = {'messages': []}
    # Query pending loan applicants
    pending = NewLoanApplicant.objects.filter(status='pending')
    context['pending_count'] = pending.count()
    # Check if the request method is POST, a CSV file is uploaded, and a selected model is provided
    if request.method == 'POST' and request.FILES.get('csv_file') and 'selected_model' in request.POST:
        try:
            # Retrieve the uploaded CSV file and selected model from the request
            csv_file = request.FILES['csv_file']
            selected_model = request.POST['selected_model']
            model = select_model(selected_model)
            csv_data = read_csv_file(csv_file)

            # Define the expected columns in the CSV file
            expected_columns = ['Age', 'Income', 'LoanAmount', 'CreditScore', 'MonthsEmployed', 'LoanTerm', 'DTIRatio']
            actual_columns = list(csv_data.columns)

            if not all(column in actual_columns for column in expected_columns):
                raise ValueError('Incorrect columns in the CSV file')
            
            # Check if the CSV file is empty
            if csv_data.empty:
                raise ValueError('The CSV file is empty')
            csv_data, records_list = apply_label_encoders(csv_data)
            context['csv_data'] = {
                'headers': list(records_list[0].keys()),
                'records': records_list,
            }
            # Make predictions using the loaded model
            predictions_data = make_predictions(model, csv_data, records_list)

            # Count predictions labeled as 0 (Approved) and 1 (Rejected)
            count_0 = 0
            count_1 = 0
            for record, prediction in zip(records_list, [prediction for _, prediction in predictions_data]):
                save_to_database([record], [prediction])
                if prediction == 0:
                    count_0 += 1
                elif prediction == 1:
                    count_1 += 1

            print("Count of 0:", count_0)
            print("Count of 1:", count_1)

            # Create a pie chart using Plotly
            labels = ['0 (Approved)', '1 (Rejected)']
            values = [count_0, count_1]
            colors = ['lightgreen', 'lightcoral']
            fig = px.pie(names=labels, values=values, color=labels, color_discrete_sequence=colors)
            plot_div = plot(fig, output_type='div', include_plotlyjs=False)

            context['predictions_data'] = {
                'headers': list(records_list[0].keys()),
                'records': predictions_data,
                'plot_div': plot_div,
                'chart_div_id': 'pie-chart-container',
            }
        except FileNotFoundError as e:
            context['error_message'] = str(e)
        except ValueError as e:
            context['error_message'] = str(e)

    context['available_models'] = get_available_models()
    return render(request, 'admin/predictions.html', context)

# contributor: Cynthia , Nazli
# The performance view provides an overview of the model's accuracy and confusion matrix on test data.
def performance(request):
    try:
        pending = NewLoanApplicant.objects.filter(status='pending')
        pending_count = pending.count()
        #get the list of available models
        available_models = get_available_models()

        if request.method == 'POST' and 'selected_model' in request.POST:
            selected_model = request.POST['selected_model']
        else:
            selected_model = available_models[0] if available_models else None

        model = select_model(selected_model)
        # Retrieve features used in training the model   
        features_used_in_training = [field.name for field in LoanApplicant._meta.fields if field.name != 'id']
        test_data = LoanApplicant.objects.all().values(*features_used_in_training)
        test_data_df = pd.DataFrame.from_records(test_data, columns=features_used_in_training)
        missing_columns = set(features_used_in_training) - set(test_data_df.columns)
        test_data_df = test_data_df.drop(columns=missing_columns, errors='ignore')

        print("Missing values in test data:")
        print(test_data_df.isnull().sum())
        print("Columns in test_data_df before handling missing columns:", test_data_df.columns)
        print("Test Data DataFrame:")
        print(test_data_df)
        print("Columns before prediction:", test_data_df.columns)

        if 'Default' not in test_data_df.columns:
            return render(request, 'performance.html', {'error': "'Default' not found in the dataset"})
        # Prepare input for prediction
        prediction_input = test_data_df.drop(['Default', 'LoanID'], axis=1)
        print("Prediction Input:")
        print(prediction_input)
         # Make predictions using the selected model
        test_prediction = model.predict(prediction_input)
        Y_test = list(test_data_df['Default'])
        Y_test = np.nan_to_num(Y_test, nan=-1)

      
        print("Before calculating accuracy")
        accuracy = accuracy_score(Y_test, test_prediction)
        print("After calculating accuracy")
        cm = confusion_matrix(Y_test, test_prediction)

        print("Columns in test_data_df after handling missing columns:", test_data_df.columns)
        print("Accuracy:", accuracy)
        print("Confusion Matrix:", cm)
        # Prepare context for rendering the template
        context = {
            'available_models': available_models,
            'selected_model': selected_model,
            'accuracy': accuracy,
            'confusion_matrix': cm,
            'columns_after_missing_handling': test_data_df.columns.tolist(),
            'pending_count': pending_count,
        }

        print("Context Data:", context)
        return render(request, 'admin/performance.html', context)
    
    except Exception as e:
        print("Error during prediction:", str(e))
        return render(request, 'admin/performance.html', {'error': f"Prediction error: {str(e)}"})


# contributor: Cynthia
#See statistical reports of all applicants
def reports(request):
    # Query pending loan applicants
    pending = NewLoanApplicant.objects.filter(status='pending')
    pending_count = pending.count()
    # Count total, approved, and rejected loan applications
    total_applications = LoanApplicant.objects.count()
    approved_applications = LoanApplicant.objects.filter(Default=0).count()
    rejected_applications = LoanApplicant.objects.filter(Default=1).count()

    # Calculate approval and rejection rates
    approval_rate = (approved_applications / total_applications) * 100 if total_applications > 0 else 0
    rejection_rate = (rejected_applications / total_applications) * 100 if total_applications > 0 else 0

    approval_rate_formatted = "{:.2f}".format(approval_rate)
    rejection_rate_formatted = "{:.2f}".format(rejection_rate)
    
    data = LoanApplicant.objects.values('Default', 'Age', 'Income', 'LoanAmount', 'CreditScore', 'MonthsEmployed', 'LoanTerm', 'DTIRatio')
    # Create a pie chart using Plotly
    labels = ['Approved', 'Rejected']
    values = [approval_rate_formatted, rejection_rate_formatted]
    fig = px.pie(values=values, names=labels, hole=0.3, title='Approval and Rejection Rates')
    plotDonut_html = fig.to_html(full_html=False)

    df = pd.DataFrame.from_records(data)
    df['Income'] /= 10
    df['LoanAmount'] /= 10

    # Calculate statistics for each feature based on loan approval status
    feature_statistics = {}
    features = ['Age', 'Income', 'LoanAmount', 'CreditScore', 'MonthsEmployed', 'LoanTerm', 'DTIRatio']

    for feature in features:
        statistics = df.groupby('Default')[feature].agg(['mean', 'median', 'min', 'max', 'std'])
        if feature in ['Income', 'LoanAmount']:
         statistics = statistics.round(2)
         statistics = statistics.astype(str) + 'kr'

        feature_statistics[feature] = statistics.to_html()

    context = {
        'total_applications': total_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        'approval_rate': approval_rate_formatted,
        'rejection_rate': rejection_rate_formatted,
        'plotDonut_html': plotDonut_html,
        'feature_statistics': feature_statistics,
        'pending_count': pending_count,
    }

    return render(request, 'admin/reports.html', context)


#contributer: Nazli
# CustomPasswordResetView is a subclass of AllauthPasswordResetView
# It provides a custom template for the password reset page.
class CustomPasswordResetView(AllauthPasswordResetView): 
    template_name = 'custom_password_reset.html'  
    success_url = reverse_lazy('password_reset_done')  

# CustomPasswordResetDoneView is a simple TemplateView subclass
# It provides a custom template for the password reset done page.
class CustomPasswordResetDoneView(TemplateView):
    template_name = 'custom_password_reset_done.html'  
 
