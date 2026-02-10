import React from "react";
import { useNavigate } from "react-router-dom";
import './App.css';

function Homepage() {
  const navigate = useNavigate();
  return (
    <div>
      <button type="button1" className='Create' onClick={() => navigate('/Creategame')}>Create Game</button><br></br>
      <button type="button1" className='Join' onClick={() => navigate('/Joingame')}>Join Game</button>
    </div>
  );
}

export default Homepage;
