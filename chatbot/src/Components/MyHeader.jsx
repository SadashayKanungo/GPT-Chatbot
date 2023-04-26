import React from "react";

const base_url = `${window.location.protocol}//${window.location.host}`;

const MyHeader = () => {
  console.log();
  return(
    <>
    <div className="react-chatbot-kit-chat-header" id="loader">
      <div className="stage">
        <div className="dot-floating"></div>
      </div>
    </div>
    <div className="react-chatbot-kit-chat-header" id="header">
      <a href={base_url} style={{"text-decoration":"None", "color":"#fff"}}>Powered  by <i> GPT Chatbot </i></a>
    </div>
    </>
  )
};

export default MyHeader;