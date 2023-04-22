console.log("Stripe Sanity check!");

// Get Stripe publishable key
fetch("/stripe/config")
.then((result) => { return result.json(); })
.then((data) => {
  // Initialize Stripe.js
  const stripe = Stripe(data.publicKey);

  // Event handler
  document.querySelector("#buyStandard").addEventListener("click", () => {
    // Get Checkout Session ID
    fetch("/stripe/create-checkout-session?plan=Standard")
    .then((result) => { return result.json(); })
    .then((data) => {
      console.log(data);
      // Redirect to Stripe Checkout
      return stripe.redirectToCheckout({sessionId: data.sessionId})
    })
    .then((res) => {
      console.log(res);
    });
  });
});

// Get Stripe publishable key
fetch("/stripe/config")
.then((result) => { return result.json(); })
.then((data) => {
  // Initialize Stripe.js
  const stripe = Stripe(data.publicKey);

  // Event handler
  document.querySelector("#buyPremium").addEventListener("click", () => {
    // Get Checkout Session ID
    fetch("/stripe/create-checkout-session?plan=Premium")
    .then((result) => { return result.json(); })
    .then((data) => {
      console.log(data);
      // Redirect to Stripe Checkout
      return stripe.redirectToCheckout({sessionId: data.sessionId})
    })
    .then((res) => {
      console.log(res);
    });
  });
});