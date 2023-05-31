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

// const bot_id = "9aea670e6ecf4bca8c3eb94e1bd76605";
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
  
  useEffect(() => {
    const observer = new MutationObserver(mutationsList => {
      mutationsList.forEach(mutation => {
        if (mutation.type === 'childList') {
          const inputElements = document.querySelectorAll('input');
          inputElements.forEach(inputElement => {
            inputElement.required = true;
          });
        }
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
    return () => {
      observer.disconnect();
    };
  }, []);

  if (isLoading) {
    return <div className='App'><strong style={{"color":"yellow"}}>Loading...</strong></div>;
  }

  if (error) {
    return <div className='App'><strong style={{"color":"red"}}>Error: {error.message}</strong></div>;
  }

  const isLightTheme = (color) => {
    // Convert hex color code to RGB
    const hex = color.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    // Calculate relative luminance using the sRGB color space formula
    const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
    // Check if the luminance is above a threshold to determine if the color is light or dark
    return (luminance > 0.5)
  }

  const getConfig = (data) => {
    document.documentElement.style.setProperty('--accentColor', data.config.accent_color);
    if(isLightTheme(data.config.accent_color)){
      document.documentElement.style.setProperty('--accentTextColor', '#000');
      // document.documentElement.style.setProperty('--messageColor', 	'#f4f4f5');
      // document.documentElement.style.setProperty('--messageTextColor', '#000');
      // document.documentElement.style.setProperty('--backgroundColor', '#000');
    } else {
      document.documentElement.style.setProperty('--accentTextColor', '#fff');
      // document.documentElement.style.setProperty('--messageColor', '#3f3f46');
      // document.documentElement.style.setProperty('--messageTextColor', '#fff');
      // document.documentElement.style.setProperty('--backgroundColor', '#fff');
    }
    
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
        header: (props) => <MyHeader {...props} text={data.config.header_text} base_url={base_url}/>,
        botAvatar: (props) => <MyBotAvator {...props} />,
      }
    };
  }
  
  return (
    
    <div className="App">
      <Chatbot
        config={getConfig(data)}
        messageParser={MessageParser}
        actionProvider= {(props) => <ActionProvider {...props} ask_url={`${base_url}/chat/ask?id=${data.qa_chain_id}`} show_sources={data.config.show_sources}/>}
      />
      <a class="banner" href={base_url} target='_blank'>Powered by <strong>Elephant.ai</strong></a>
    </div>
    
    
  );
}

export default App;
