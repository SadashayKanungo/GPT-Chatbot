console.log("Stripe Sanity check!");

// Get Stripe publishable key
fetch("/stripe/config")
.then((result) => { return result.json(); })
.then((data) => {
  // Initialize Stripe.js
  // console.log(data);
  const stripe = Stripe(data.publicKey);

  // Event handler
  const btns = document.querySelectorAll('.stripe-subscribe-btn');
  btns.forEach(btn => {
    var plan = btn.getAttribute('data-plan');
    // console.log(plan);
    btn.addEventListener("click", () => {
      // Get Checkout Session ID
      fetch(`/stripe/create-checkout-session?plan=${plan}`)
      .then((response) => {
        if (response.ok) {
          return response.json();
        } else {
          response.json().then(data => {
            const errorMessage = data.error;
            console.log(errorMessage);
            const errorParagraph = document.querySelector('#subscribe_error');
            errorParagraph.innerText = errorMessage;
            errorParagraph.classList.remove("error--hidden");
            setTimeout(()=>{
              errorParagraph.innerText = "";
              errorParagraph.classList.add("error--hidden");
            }, 10000);
          })
        }
      })
      .then((data) => {
        // console.log(data);
        // Redirect to Stripe Checkout
        return stripe.redirectToCheckout({sessionId: data.sessionId})
      });
    });
  });
});

// Event handler
const btns = document.querySelectorAll('.stripe-cancel-btn');
btns.forEach(btn => {
  btn.addEventListener("click", () => {
    // Get Checkout Session ID
    fetch(`/cancelsubscription`)
    .then((result) => { return result.json(); })
    .then(() => {
      window.location.reload()
    });
  });
});