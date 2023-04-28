import React, {useEffect, useState} from 'react';
import axios from 'axios';

import Chatbot, { createChatBotMessage, createClientMessage } from 'react-chatbot-kit';
import 'react-chatbot-kit/build/main.css';
import './App.css';

import MyHeader from './Components/MyHeader';
import MyBotAvator from './Components/MyBotAvator';
import MessageParser from './MessageParser.js';
import ActionProvider from './ActionProvider.js';

const urlParams = new URLSearchParams(window.location.search);
const bot_id = urlParams.get('id');
const base_url = `${window.location.protocol}//${window.location.host}`;

// const bot_id = "5561514bf2124754a17fd5bf8d1f6d2f";
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

  const textColor = (color) => {
    // Convert hex color code to RGB
    const hex = color.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    // Calculate relative luminance using the sRGB color space formula
    const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
    // Check if the luminance is above a threshold to determine if the color is light or dark
    if (luminance > 0.5) {
      return '#000';
    } else {
      return '#fff';
    }
  }

  const getConfig = (data) => {
    document.documentElement.style.setProperty('--accentColor', data.config.accent_color);
    document.documentElement.style.setProperty('--accentTextColor', textColor(data.config.accent_color));
    var greet_messages = data.config.initial_messages.map((msg) => createChatBotMessage(msg));
    var init_messages = greet_messages.concat(data.messages.map((msg) => {
      if(msg.role === "user") {
        return createClientMessage(msg.content);
      } else {
        return createChatBotMessage(msg.content);
      }
    }));

    return {
      initialMessages: init_messages,
      botName: "GPT Chatbot",
      customComponents: {
        header: (props) => <MyHeader {...props} text={data.config.header_text}/>,
        botAvatar: (props) => <MyBotAvator {...props} />,
      }
    };
  }
  
  return (
    
    <div className="App">
      <Chatbot
        config={getConfig(data)}
        messageParser={MessageParser}
        actionProvider= {(props) => <ActionProvider {...props} ask_url={`${base_url}/chat/ask?id=${data.qa_chain_id}`} />}
      />
      <a class="banner" href={base_url} target='blank'>Powered by <strong>GPTChatbot</strong></a>
    </div>
    
    
  );
}

export default App;
