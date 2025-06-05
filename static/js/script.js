document.addEventListener("DOMContentLoaded", function() {
    const loginForm = document.querySelector("form");
    if (loginForm) {
        loginForm.addEventListener("submit", function(event) {
            const email = document.querySelector("input[name='email']").value;
            const password = document.querySelector("input[name='password']").value;
            
            if (email.trim() === "" || password.trim() === "") {
                alert("Email and Password cannot be empty!");
                event.preventDefault(); // Stop form submission
            }
        });
    }
});

