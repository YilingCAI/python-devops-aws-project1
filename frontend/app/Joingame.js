import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

function Joingame() {
  const [username, setUsername] = useState('');
  const [gameId, setGameId] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleJoinGame = async (e) => {
    e.preventDefault();
    const payload = {
      username: username,
      game_id: gameId
    };

    try {
      const response = await axios.post('http://3.139.54.170:8000/join_game', payload);
      console.log(response.data);
      if (response.data.message === 'Joined game') {
        setError('');
        navigate(`/Game/${username}/${gameId}/O`); // Use 'O' for Player 2
      } else {
        setError('Failed to join game');
      }
    } catch (error) {
      if (error.response) {
        setError(error.response.data.message || 'Failed to join game');
      } else {
        setError('An error occurred. Please try again.');
      }
    }
  };

  return (
    <div>
      <h1>Join Game</h1>
      <form onSubmit={handleJoinGame}>
        <label>
          Username:
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
        </label>
        <label>
          Game ID:
          <input
            type="text"
            value={gameId}
            onChange={(e) => setGameId(e.target.value)}
            required
          />
        </label>
        <button type="submit">Confirm</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </form>
    </div>
  );
}

export default Joingame;
