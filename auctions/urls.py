from django.urls import path

from . import views

app_name="auctions"
urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("user_listings/", views.user_listings, name="user_listings"),
    path("add_listing/", views.add_listing, name="add_listing"),
    path("listings/<int:listing_id>/", views.listing_page, name="listing_page"),
    path("watchlist/", views.watchlist, name="watchlist"),
]
