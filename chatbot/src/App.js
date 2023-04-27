import React, {useEffect, useState} from 'react';
import axios from 'axios';

import Chatbot, { createChatBotMessage, createClientMessage } from 'react-chatbot-kit';
import 'react-chatbot-kit/build/main.css';
import './App.css';

import config from './config.js';
import MessageParser from './MessageParser.js';
import ActionProvider from './ActionProvider.js';

const urlParams = new URLSearchParams(window.location.search);
const bot_id = urlParams.get('id');
const base_url = `${window.location.protocol}//${window.location.host}`;

// const bot_id = "c3247c990b8b4500b265dbd049ef5f09";
// const base_url = `http://localhost:5000`;

function App() {
  const [data, setData] = useState({qa_chain_id:null, messages:null});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // API call before component renders
    axios.get(`${base_url}/chat/start?id=${bot_id}`)
      .then(response => {
        setData(response.data);
        setIsLoading(false);
      })
      .catch(error => {
        setError(error);
        setIsLoading(false);
      });
  }, []);

  if (isLoading) {
    return <div className='App'><strong style={{"color":"yellow"}}>Loading...</strong></div>;
  }

  if (error) {
    return <div className='App'><strong style={{"color":"red"}}>Error: {error.message}</strong></div>;
  }

  const getInitialMessages = (config_messages, data_messages) => {
    return config_messages.concat(data_messages.map((msg) => {
      if(msg.role === "user") {
        return createClientMessage(msg.content);
      } else {
        return createChatBotMessage(msg.content);
      }
    }));
  }
  
  return (
    
    <div className="App">
      <Chatbot
        config={{
          ...config,
          initialMessages: getInitialMessages(config.initialMessages, data.messages),
        }}
        messageParser={MessageParser}
        actionProvider= {(props) => <ActionProvider {...props} ask_url={`${base_url}/chat/ask?id=${data.qa_chain_id}`} />}
      />
    </div>
    
    
  );
}

export default App;
