import React from "react";

const MyHeader = ({text}) => {
  console.log();
  return(
    <>
    <div className="react-chatbot-kit-chat-header" id="loader">
      <div className="stage">
        <div className="dot-floating"></div>
      </div>
    </div>
    <div className="react-chatbot-kit-chat-header" id="header">
      {text}
    </div>
    </>
  )
};

export default MyHeader;