import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function Signup() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate(); 

  const handleSignup = async (e) => {
    e.preventDefault();
    const payload = { username, password };

    try {
      const response = await axios.post('http://3.139.54.170:8000/register', payload);
      console.log(response.data);
      if (response.data.message === 'User registered successfully!') {
        setError('');
        navigate('/Login');
      } else if (response.data.message === 'Username or email already exists!') {
        setError('Username already exists');
      }
    } catch (error) {
      if (error.response) {
        setError(error.response.data.message || 'Invalid registration details');
      } else {
        setError('An error occurred. Please try again.');
      }
    }
  };

  return (
    <div>
      <h1>Signup</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSignup}>
        <div>
          <label>
            Username:
            <input 
              type="text" 
              value={username} 
              onChange={(e) => setUsername(e.target.value)}
              required 
            />
          </label>
        </div>
        <div>
          <label>
            Password:
            <input 
              type="password" 
              value={password} 
              onChange={(e) => setPassword(e.target.value)}
              required 
            />
          </label>
        </div>
        <button type="submit">Sign up</button>
      </form>
    </div>
  );
}

export default Signup;
