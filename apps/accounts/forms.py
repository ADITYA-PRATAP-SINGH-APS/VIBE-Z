from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator


User = get_user_model()


class LoginForm(forms.Form):
    unique_name = forms.CharField(max_length=12)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        unique_name = cleaned.get("unique_name")
        password = cleaned.get("password")
        if unique_name and password:
            user = authenticate(unique_name=unique_name, password=password)
            if not user:
                raise forms.ValidationError("Invalid unique name or password.")
            cleaned["user"] = user
        return cleaned


class RegisterForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    age = forms.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)])
    gender = forms.ChoiceField(choices=[("male", "Male"), ("female", "Female"), ("other", "Other")])
    email = forms.EmailField()
    unique_name = forms.CharField(
        max_length=12,
        validators=[
            RegexValidator(
                regex=r"^\S{1,12}$",
                message="Unique name must be up to 12 characters with no spaces.",
            )
        ],
    )
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)

    def clean_unique_name(self):
        unique_name = self.cleaned_data["unique_name"].strip()
        if User.objects.filter(unique_name=unique_name).exists():
            raise forms.ValidationError("That unique name is already taken.")
        return unique_name

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password_confirm"):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned

    def save(self):
        user = User.objects.create_user(
            unique_name=self.cleaned_data["unique_name"],
            password=self.cleaned_data["password"],
            email=self.cleaned_data["email"],
            full_name=self.cleaned_data["full_name"],
        )
        profile = user.profile
        profile.age = self.cleaned_data["age"]
        profile.gender = self.cleaned_data["gender"]
        profile.save(update_fields=["age", "gender"])
        return user
