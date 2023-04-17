import React from 'react';
import { createChatBotMessage } from 'react-chatbot-kit';
import MyBotAvator from './Components/MyBotAvator';

// const bot_name = window.gpt_chatbot.name;
const bot_name = 'GPTbot'

const config = {
  initialMessages: [createChatBotMessage(`Hello there!`)],
  botName: bot_name,
  customComponents: {
    botAvatar: (props) => <MyBotAvator {...props} />,
  }
};

export default config;