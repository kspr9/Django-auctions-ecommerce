from django.contrib.auth.models import AbstractUser
from django.db import models



class User(AbstractUser):
    """User model - inherited from Django implementation"""
    """
    # Model fields:
        username
        first_name
        last_name
        email
        is_staff
        is_active
        date_joined
    """
    pass


class Bid(models.Model):
    # Model fields
    # auto: bid_id
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bidder", null=True)
    bid_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    #bids_listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="bids_listing")
    bid_date = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "bid"
        verbose_name_plural = "bids"
    
    def __str__(self):
        return f"{self.bidder} bid {self.bid_price}€ on {self.bid_date}"


class Listing(models.Model):
    """
        Listing model contains all info related to one listing excluding data about bids (who bid how much etc.)
    """
    # Categoriy choices
    A = 'WIZARDING CLOTHING'
    B = 'BROOMS'
    C = 'WANDS'
    D = 'MAGICAL BOOKS'
    E = 'MAGICAL ITEMS'
    F = 'MYTHICAL ITEMS'

    LISTING_CATEGORY_CHOICES = [
        (A, 'Wizarding Clothing'),
        (B, 'Brooms'),
        (C, 'Wands'),
        (D, 'Magical Books'),
        (E, 'Magical Items'),
        (F, 'Mythical Items'),
    ]

    # Model fields
    # auto: listing_id
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=64, blank=False)
    description = models.TextField()
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    image_url = models.URLField(max_length=300, blank=True)
    listing_category = models.CharField(
        max_length=36,
        choices=LISTING_CATEGORY_CHOICES,
        default=B,
    )
    publication_date = models.DateTimeField(auto_now_add=True, null=True)
    closed = models.BooleanField(default=False)
    #comments = models.ManyToManyField(Comment, blank=True, related_name="comments")
    bids = models.ManyToManyField(Bid, blank=True, related_name="bids")
    winner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        blank=True, null=True,
        related_name="winner")
    
    # TODO add coundown timer for auction end date

    class Meta:
        verbose_name = "auction"
        verbose_name_plural = "auctions"
    
    def __str__(self):
        return f"Listing {self.id}> title: {self.title}, seller: {self.seller}, current price: {self.current_price}€"


class Comment(models.Model):
    # Model fields
    # auto: comment_id
    comments_listing = models.ForeignKey(Listing, on_delete=models.CASCADE, null=True)
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    comment = models.TextField(blank=False, null=True)
    comment_date = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "comment"
        verbose_name_plural = "comments"
    
    def __str__(self):
        return f"Comment {self.id} on listing {self.comments_listing} made by {self.commenter}"


class UsersWatchlist(models.Model):
    watchlist_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True,  related_name="watchlist")
    listing_in_watchlist = models.ForeignKey(Listing, on_delete=models.CASCADE, null=True, related_name="watchlist")

    # Forces to not have listing duplicates for one user
    unique_together = ["listing_in_watchlist", "watchlist_user"]

    def __str__(self):
        return f"{self.listing_in_watchlist} in user {self.watchlist_user} watchlist"