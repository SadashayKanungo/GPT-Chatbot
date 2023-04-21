import React from 'react';
import { createChatBotMessage } from 'react-chatbot-kit';
import MyHeader from './Components/MyHeader';
import MyBotAvator from './Components/MyBotAvator';

// const bot_name = window.gpt_chatbot.name;
const bot_name = 'GPT chatbot'

const config = {
  initialMessages: [createChatBotMessage(`Hello there!`)],
  botName: bot_name,
  customComponents: {
    header: (props) => <MyHeader {...props} isLoading={false}/>,
    botAvatar: (props) => <MyBotAvator {...props} />,
  }
};

export default config;