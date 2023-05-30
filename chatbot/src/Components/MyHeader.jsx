import React from "react";
import axios from 'axios';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faRefresh } from '@fortawesome/free-solid-svg-icons'

const MyHeader = ({text, base_url}) => {
  function clearCookieAndReload() {
    console.log("refresh");
    axios.get(`${base_url}/chat/refresh`)
    .then(response => {
      window.location.reload();
    }).catch(err => {
      console.log(err);
    });
  }

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