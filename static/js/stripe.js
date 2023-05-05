console.log("Stripe Sanity check!");

// Get Stripe publishable key
fetch("/stripe/config")
.then((result) => { return result.json(); })
.then((data) => {
  // Initialize Stripe.js
  // console.log(data);
  const stripe = Stripe(data.publicKey);

  // Event handler
  const btns = document.querySelectorAll('.stripe-btn');
  btns.forEach(btn => {
    var plan = btn.getAttribute('data-plan');
    // console.log(plan);
    btn.addEventListener("click", () => {
      // Get Checkout Session ID
      fetch(`/stripe/create-checkout-session?plan=${plan}`)
      .then((result) => { return result.json(); })
      .then((data) => {
        // console.log(data);
        // Redirect to Stripe Checkout
        return stripe.redirectToCheckout({sessionId: data.sessionId})
      })
      .then((res) => {
        // console.log(res);
      });
    });
  });
});