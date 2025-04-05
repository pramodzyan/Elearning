// Main JavaScript file for Educational Platform

// Document ready function
document.addEventListener('DOMContentLoaded', function() {
    console.log('Educational Platform JS loaded');
    
    // Quiz choice selection
    setupQuizChoices();
    
    // Quiz timer if applicable
    setupQuizTimer();
    
    // Toggle password visibility in auth forms
    setupPasswordToggle();
});

// Function to handle quiz choice selection
function setupQuizChoices() {
    const choiceItems = document.querySelectorAll('.choice-item');
    if (choiceItems.length === 0) return;
    
    choiceItems.forEach(item => {
        item.addEventListener('click', function() {
            // Get the parent question container
            const questionContainer = this.closest('.question-card');
            
            // Remove selected class from all choices in this question
            questionContainer.querySelectorAll('.choice-item').forEach(choice => {
                choice.classList.remove('selected');
            });
            
            // Add selected class to clicked choice
            this.classList.add('selected');
            
            // Set the radio button as checked
            const radio = this.querySelector('input[type="radio"]');
            if (radio) {
                radio.checked = true;
            }
        });
    });
}

// Function to setup quiz timer
function setupQuizTimer() {
    const timerElement = document.getElementById('quiz-timer');
    if (!timerElement) return;
    
    const timeLimit = parseInt(timerElement.dataset.timeLimit || 0, 10);
    if (!timeLimit) return;
    
    let timeRemaining = timeLimit * 60; // Convert minutes to seconds
    
    // Update timer every second
    const timerInterval = setInterval(function() {
        timeRemaining--;
        
        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            document.getElementById('quiz-form').submit();
            return;
        }
        
        // Format time as MM:SS
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        
        timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Add warning class when time is running low
        if (timeRemaining < 60) {
            timerElement.classList.add('text-danger');
        }
    }, 1000);
}

// Function to toggle password visibility
function setupPasswordToggle() {
    const toggleButtons = document.querySelectorAll('.password-toggle');
    if (toggleButtons.length === 0) return;
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const passwordField = document.getElementById(this.dataset.target);
            
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                this.innerHTML = '<i class="bi bi-eye-slash"></i>';
            } else {
                passwordField.type = 'password';
                this.innerHTML = '<i class="bi bi-eye"></i>';
            }
        });
    });
}

// Function to mark a subtopic as reviewed
function markAsReviewed(subtopicId) {
    // Send a POST request to mark the subtopic as reviewed
    fetch(`/mark-as-reviewed/${subtopicId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reviewed: true }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI to show reviewed status
            const button = document.getElementById(`review-btn-${subtopicId}`);
            button.classList.remove('btn-primary');
            button.classList.add('btn-success');
            button.textContent = 'Reviewed ✓';
            button.disabled = true;
        }
    })
    .catch(error => {
        console.error('Error marking subtopic as reviewed:', error);
    });
}

// Helper function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}