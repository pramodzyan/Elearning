from django import template
from django.template.defaultfilters import stringfilter
import re

register = template.Library()

@register.filter
@stringfilter
def youtube_embed(url):
    """
    Converts a YouTube watch URL to an embed URL.
    Example:
    https://www.youtube.com/watch?v=12345678901 -> https://www.youtube.com/embed/12345678901
    https://youtu.be/12345678901 -> https://www.youtube.com/embed/12345678901
    """
    if not url:
        return ''
    
    # Match YouTube URL patterns
    youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(youtube_regex, url)
    
    if match:
        video_id = match.group(1)
        return f'https://www.youtube.com/embed/{video_id}'
    
    # Return original URL if no match found
    return url

@register.filter
def get_item(dictionary, key):
    """
    Gets an item from a dictionary by key.
    Used for accessing dictionary values in templates where variable keys are needed.
    """
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def div(value, arg):
    """
    Divides the value by the argument
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """
    Multiplies the value by the argument
    """
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0
