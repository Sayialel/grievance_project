document.addEventListener('DOMContentLoaded', function() {
  // Initialize tab handling
  const tabElements = document.querySelectorAll('#adminTabs button');

  // Setup tab click handling
  tabElements.forEach(function(tabElement) {
    tabElement.addEventListener('click', function(event) {
      event.preventDefault();
      const targetTab = document.querySelector(this.getAttribute('data-bs-target'));

      // Hide all tab panes
      document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('show', 'active');
      });

      // Deactivate all tabs
      tabElements.forEach(tab => {
        tab.classList.remove('active');
        tab.setAttribute('aria-selected', 'false');
      });

      // Activate the clicked tab
      this.classList.add('active');
      this.setAttribute('aria-selected', 'true');

      // Show the target tab content
      targetTab.classList.add('show', 'active');
    });
  });

  // Handle links to tabs
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', function(event) {
      event.preventDefault();
      const targetId = this.getAttribute('href').substring(1);
      const tabButton = document.querySelector(`button[data-bs-target="#${targetId}"]`);

      if (tabButton) {
        tabButton.click();
      }
    });
  });

  // Check for hash in URL and activate corresponding tab
  if (window.location.hash) {
    const hash = window.location.hash.substring(1);
    const tabButton = document.querySelector(`button[data-bs-target="#${hash}"]`);

    if (tabButton) {
      tabButton.click();
    }
  }
});