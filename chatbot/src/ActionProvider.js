import React from 'react';
import axios from 'axios';


const ActionProvider = ({ createChatBotMessage, setState, children, ask_url, show_sources}) => {
  // console.log(ask_url);
  const handleQuery = async (question) => {
    document.getElementById("header").style.display = "none";
    document.getElementById("loader").style.display = "flex";
    
    try {
      const {data} = await axios.post(ask_url, {question});
      const botMessage = createChatBotMessage(data.answer);
      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, botMessage],
      }));
      if(show_sources && data.sources.length){
        const botMessageSrc = createChatBotMessage(
          <span class="sources"> Sources: 
            {data.sources.map((src,i) => <a href={src}>{i+1}</a>)}
          </span>
        );
        setState((prev) => ({
          ...prev,
          messages: [...prev.messages, botMessageSrc],
        }));
      }
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