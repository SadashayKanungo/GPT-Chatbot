import React from "react";

const MyHeader = () => {
  console.log();
  return(
    <>
    <div className="react-chatbot-kit-chat-header" id="loader">
      <div className="stage">
        <div className="dot-floating"></div>
      </div>
    </div>
    <div className="react-chatbot-kit-chat-header" id="header">Conversation with GPT Chatbot</div>
    </>
  )
};

export default MyHeader;