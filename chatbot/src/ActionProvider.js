import React from 'react';
import axios from 'axios';

const urlParams = new URLSearchParams(window.location.search);
const qa_chain_id = urlParams.get('id');
const ask_url = `http://${window.location.host}/chat/ask`;

console.log(ask_url, qa_chain_id);


const ActionProvider = ({ createChatBotMessage, setState, children }) => {
  const handleQuery = async (question) => {
    document.getElementById("header").style.display = "none";
    document.getElementById("loader").style.display = "flex";
    
    try {
      const {data} = await axios.post(ask_url, {question, qa_chain_id});
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
    
    document.getElementById("loader").style.display = "none";
    document.getElementById("header").style.display = "flex";
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