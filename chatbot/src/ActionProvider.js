// in ActionProvider.jsx
import React from 'react';
import axios from 'axios';

// const ASK_URL = window.gpt_chatbot.ask_url;
const ASK_URL = `http://localhost:5000/bot/ask?id=643c888f0722a1dde9026961`;

const ActionProvider = ({ createChatBotMessage, setState, children }) => {
  const handleQuery = async (question) => {
    try {
      const {data} = await axios.post(ASK_URL, {question});
      const botMessage = createChatBotMessage(data.answer);
      
      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, botMessage],
      }));
    } catch (error) {
      const botError = createChatBotMessage("An error occured :(");
      console.error(error.message);
      
      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, botError],
      }));
    }
  };

  // Put the handleHello function in the actions object to pass to the MessageParser
  return (
    <div>
      {React.Children.map(children, (child) => {
        return React.cloneElement(child, {
          actions: {
            handleQuery,
          },
        });
      })}
    </div>
  );
};

export default ActionProvider;