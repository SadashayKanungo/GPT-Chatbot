const CHAT_BUTTON_SIZE = 50 // size of the chat button in pixels
const CHAT_BUTTON_RADIUS = CHAT_BUTTON_SIZE / 2 // radius of the chat button in pixels
const CHAT_BUTTON_BACKGROUND_COLOR = 'black' // background color of the chat button
let ICON_COLOR = 'white'
let has_been_opened = false

// create the chat button element
const chatButton = document.createElement('div')
// apply styles to the chat button
chatButton.style.position = 'fixed'
chatButton.style.bottom = '20px'
chatButton.style.right = '20px'
chatButton.style.width = CHAT_BUTTON_SIZE + 'px'
chatButton.style.height = CHAT_BUTTON_SIZE + 'px'
chatButton.style.borderRadius = CHAT_BUTTON_RADIUS + 'px'
chatButton.style.backgroundColor = CHAT_BUTTON_BACKGROUND_COLOR
chatButton.style.boxShadow = '0 4px 8px 0 rgba(0, 0, 0, 0.2)'
chatButton.style.cursor = 'pointer'
chatButton.style.zIndex = 999999998
chatButton.style.transition = 'all .2s ease-in-out'



chatButton.addEventListener('mouseenter', (event) => {
  chatButton.style.transform = 'scale(1.08)'
})
chatButton.addEventListener('mouseleave', (event) => {
  chatButton.style.transform = 'scale(1)'
})

// create the chat button icon element
const chatButtonIcon = document.createElement('div')

// apply styles to the chat button icon
chatButtonIcon.style.display = 'flex'
chatButtonIcon.style.alignItems = 'center'
chatButtonIcon.style.justifyContent = 'center'
chatButtonIcon.style.width = '100%'
chatButtonIcon.style.height = '100%'
chatButtonIcon.style.zIndex = 999999999

// add the chat button icon to the chat button element

chatButton.appendChild(chatButtonIcon)

// add the chat button to the page

// toggle the chat component when the chat button is clicked
chatButton.addEventListener('click', () => {
  // toggle the chat component
  if (chat.style.display === 'none') {
    has_been_opened = true
    chat.style.display = 'flex'

    chatButtonIcon.innerHTML = getChatButtonCloseIcon()
  } else {
    chat.style.display = 'none'
    chatButtonIcon.innerHTML = getChatButtonIcon()
  }
})



const chat = document.createElement('div')

chat.style.position = 'fixed'
chat.style.flexDirection = 'column'
chat.style.justifyContent = 'space-between'
chat.style.bottom = '80px'
chat.style.width = '85vw'
chat.style.height = '70vh'
chat.style.boxShadow =
  'rgba(150, 150, 150, 0.2) 0px 10px 30px 0px, rgba(150, 150, 150, 0.2) 0px 0px 0px 1px'

chat.style.display = 'none'
chat.style.borderRadius = '10px'
chat.style.zIndex = 999999999
chat.style.overflow = 'hidden'

document.body.appendChild(chat)

// Create a condition that targets viewports at least 768px wide
const mediaQuery = window.matchMedia('(min-width: 550px)')

function handleChatWindowSizeChange(e) {
  // Check if the media query is true
  if (e.matches) {
    chat.style.height = '500px'
    chat.style.width = '400px'
  }
}

// Register event listener
mediaQuery.addEventListener('change', handleChatWindowSizeChange)

// Initial check
handleChatWindowSizeChange(mediaQuery)

const getChatbot = async () => {
  ////////////////////////////////////////// NEW STUFF //////////////////////////////////////////
  const bot_id = document.currentScript.id;
  var l = document.createElement('a');
  l.href = document.currentScript.src;
  const bot_url = `${l.protocol}//${l.host}/bot?id=${bot_id}`;
  chat.innerHTML = `<iframe id="gpt-chatbot-iframe" src="${bot_url}" width="400px" height="500px" frameborder="0""></iframe>`
  // chat.innerHTML = `<iframe id="gpt-chatbot-iframe" src="http://localhost:3000?id=${qa_chain_id}" width="100%" height="100%" frameborder="0"></iframe>`
  
  var mql = window.matchMedia("(max-width: 767px)")
  mql.addEventListener("change", (media) => {
    var iframe = document.getElementById('gpt-chatbot-iframe');
    if (media.matches) { // If media query matches
      iframe.style.width = "90%";
      iframe.style.height = "80%";
    } else {
      iframe.style.width = "400px";
      iframe.style.height = "500px";
    }
  });

  //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
  chatButton.style.backgroundColor = CHAT_BUTTON_BACKGROUND_COLOR
  
  chatButton.style.right = '20px'
  chatButton.style.left = 'unset'
  chat.style.right = '20px'
  chat.style.left = 'unset'
  

  document.body.appendChild(chatButton)

  const iconColor = getContrastingTextColor(CHAT_BUTTON_BACKGROUND_COLOR)
  ICON_COLOR = iconColor
  chatButtonIcon.innerHTML = getChatButtonIcon()

}

function getChatButtonIcon() {
  const CHAT_BUTTON_ICON = `
  <svg id="chatIcon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.3" stroke="${ICON_COLOR}" width="24" height="24">
  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.76c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 011.037-.443 48.282 48.282 0 005.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
  </svg>`

  return CHAT_BUTTON_ICON
}

function getChatButtonCloseIcon() {
  const CHAT_BUTTON_CLOSE_ICON = `
  <svg id="closeIcon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.3" stroke="${ICON_COLOR}" width="24" height="24">
    <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
  </svg>
  `
  return CHAT_BUTTON_CLOSE_ICON
}

function getContrastingTextColor(bgColor) {
  // Ensure the input is in the format #RRGGBB
  if (bgColor.charAt(0) === '#') {
    bgColor = bgColor.substr(1)
  }

  // Convert the input color to RGB
  const r = parseInt(bgColor.substr(0, 2), 16)
  const g = parseInt(bgColor.substr(2, 2), 16)
  const b = parseInt(bgColor.substr(4, 2), 16)

  // Calculate the luminance value using the WCAG formula
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

  // Return the appropriate text color based on the luminance value
  return luminance > 0.5 ? 'black' : 'white'
}

getChatbot()