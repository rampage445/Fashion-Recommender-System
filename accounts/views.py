from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout

# Create your views here.
def reg(request):
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        password1 = request.POST['pass']
        password2 = request.POST['re_pass']
        if len(name)<4:
            return render(request,'register.html',{'usermsg':"Username must be atleast 4 characters long!"})
        if '@' not in email or len(email)==0:
            return render(request,'register.html',{'emsg':"Invalid email"})
        if not password1 or not password2 or password1!=password2:
            #return redirect('/accounts/register',{'msg':"Password's don't match!"})
            return render(request,'register.html',{'passmsg':"Password's don't match or password is empty!"})
        else:
            user = User.objects.create_user(username=name,email=email,password=password1)
            user.save()
            return redirect('/')
    return render(request,'register.html')

def log(request):
    if request.method == 'POST':
        name = request.POST['your_name']
        password1 = request.POST['your_pass']
        user = authenticate(username=name,password=password1)
       
        if user is not None:
            login(request,user)
            return redirect('/')
        else:
            return render(request,'login.html',{'msg':"Login credentials don't match"})
    return render(request,'login.html')

def logo(request):
    logout(request)
    return redirect('/')