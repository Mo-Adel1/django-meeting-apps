from django.db import models

class TimeZoneChoices(models.TextChoices):
    CAIRO = "Africa/Cairo", "Cairo"
    NAIROBI = "Africa/Nairobi", "Nairobi"
    LONDON = "Europe/London", "London"
    PARIS = "Europe/Paris", "Paris"
    NEW_YORK = "America/New_York", "New York"
    LOS_ANGELES = "America/Los_Angeles", "Los Angeles"
    TOKYO = "Asia/Tokyo", "Tokyo"
    SYDNEY = "Australia/Sydney", "Sydney"

class MeetingSettings(models.Model):
    
    timezone = models.CharField(
        max_length=100, 
        choices=TimeZoneChoices.choices, 
        default=TimeZoneChoices.CAIRO, 
        help_text="Timezone for the meeting."
    )
    
    host_video = models.BooleanField(default=True, help_text="Enable host video.")
    participant_video = models.BooleanField(default=False, help_text="Enable participant video.")
    audio = models.CharField(max_length=50, default="voip", help_text="Audio type (e.g., voip).")
    auto_recording = models.CharField(max_length=50, default="cloud", help_text="Auto-recording setting.")
    waiting_room = models.BooleanField(default=True, help_text="Enable waiting room.")
    join_before_host = models.BooleanField(default=False, help_text="Allow participants to join before the host.")
    mute_upon_entry = models.BooleanField(default=True, help_text="Mute participants upon entry.")
    approval_type = models.IntegerField(default=2, help_text="Approval type for registrants.")
    closed_caption = models.BooleanField(default=True, help_text="Enable closed captioning.")
    registrants_email_notification = models.BooleanField(default=True, help_text="Notify registrants via email.")

    def __str__(self):
        return f"Meeting Settings for {self.timezone}"

    class Meta:
        verbose_name = "Meeting Settings"
        verbose_name_plural = "Meeting Settings"
