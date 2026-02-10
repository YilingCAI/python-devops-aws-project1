import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate(); 

  const handleLogin = async (e) => {
    e.preventDefault();
    const payload = { username, password };

    try {
      const response = await axios.post('http://3.139.54.170:8000/get-user-details', payload);
      console.log(response.data);
      if (response.data.status === 'success') {
        setError('');
        navigate('/Homepage');
      } else {
        setError('Invalid username or password');
      }
    } catch (error) {
      if (error.response) {
        setError(error.response.data.message || 'Invalid username or password');
      } else {
        setError('An error occurred. Please try again.');
      }
    }
  };

  return (
    <div>
      <form onSubmit={handleLogin}>
        <h2>Login</h2>
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
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" className="log">Login</button>
        <button type="button" className="sig" onClick={() => navigate('/signup')}>Sign up</button>
      </form>
    </div>
  );
}

export default Login;
