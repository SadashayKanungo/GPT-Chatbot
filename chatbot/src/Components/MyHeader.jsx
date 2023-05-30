import React from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faRefresh } from '@fortawesome/free-solid-svg-icons'

function clearCookieAndReload() {
  console.log("refresh");
  // Set the cookie's expiration date in the past to delete it
  document.cookie = "gptchatbot_cookie=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  // Reload the page
  window.location.reload();
}

const MyHeader = ({text}) => {
  return(
    <>
    <div className="react-chatbot-kit-chat-header" id="loader">
      <div className="stage">
        <div className="dot-floating"></div>
      </div>
    </div>
    <div className="react-chatbot-kit-chat-header" id="header">
        <span className="header-text">{text}</span>
        <button className="clear-btn" onClick={clearCookieAndReload}><FontAwesomeIcon icon={faRefresh} /></button>
    </div>
    </>
  )
};

export default MyHeader;