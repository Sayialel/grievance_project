from django.db.models import Count
from accounts.models import UserProfile

def auto_assign_officer(complaint):
    """
    Auto-assign a complaint to an officer based on location and workload

    The function will:
    1. Filter officers by the complaint's location
    2. Select the officer with the fewest active complaints
    3. Assign the complaint to that officer

    Returns:
        The assigned officer or None if no officers are available for the location
    """
    # Skip if already assigned
    if complaint.assigned_officer is not None:
        return complaint.assigned_officer

    # Get all officers in the complaint's location
    officers = UserProfile.objects.filter(
        role='officer',
        location=complaint.location
    )

    if not officers.exists():
        # No officers available for this location
        return None

    # Find the officer with the fewest active complaints
    officer_with_fewest = None
    min_complaints = float('inf')

    for officer in officers:
        active_complaints_count = officer.get_active_complaints_count()
        if active_complaints_count < min_complaints:
            min_complaints = active_complaints_count
            officer_with_fewest = officer

    # Assign the complaint to the selected officer
    complaint.assigned_officer = officer_with_fewest
    complaint.save(update_fields=['assigned_officer'])

    return officer_with_fewest
