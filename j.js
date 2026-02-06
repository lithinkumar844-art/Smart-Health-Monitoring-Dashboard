import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

// Mock API base for visualization
const API_BASE = 'mock';

const stripePromise = loadStripe('your_publishable_key'); // Replace with your Stripe publishable key

function CheckoutForm({ bookingId, amount }) {
  const stripe = useStripe();
  const elements = useElements();
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!stripe || !elements) return;

    try {
      // Mock API response
      const data = { client_secret: 'mock_client_secret' };

      // Simulate Stripe payment confirmation
      setTimeout(() => {
        setMessage(`Payment successful for booking ID ${bookingId}, amount $${amount}!`);
      }, 1000);
    } catch (err) {
      setMessage('Payment failed: ' + err.message);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <CardElement style={{ marginBottom: '10px' }} />
      <button type="submit" style={{ padding: '10px 20px', backgroundColor: 'green', color: 'white', borderRadius: '5px', border: 'none' }}>
        Pay ${amount}
      </button>
      {message && <div style={{ marginTop: '10px', color: 'blue' }}>{message}</div>}
    </form>
  );
}

function PaymentPage({ bookingId, amount }) {
  return (
    <Elements stripe={stripePromise}>
      <CheckoutForm bookingId={bookingId} amount={amount} />
    </Elements>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/payment/:bookingId" element={<PaymentPage bookingId={123} amount={50} />} />
      </Routes>
    </Router>
  );
}

// Render React app
const container = document.getElementById('root');
const root = createRoot(container);
root.render(<App />);
