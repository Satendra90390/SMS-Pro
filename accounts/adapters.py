from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

        email = sociallogin.account.extra_data.get('email', '')
        if not email:
            return

        from accounts.models import User
        user = User.objects.filter(email=email).first()
        if user:
            sociallogin.connect(request, user)

    def on_user_signed_up(self, request, sociallogin, **kwargs):
        request.session['oauth_new'] = True
