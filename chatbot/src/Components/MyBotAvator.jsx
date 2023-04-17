import React from "react";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faRobot } from '@fortawesome/free-solid-svg-icons'

const MyBotAvator = () => {
    return(
        <div className="custom-bot-avator">
            <FontAwesomeIcon icon={faRobot} />
        </div>
    )
}

export default MyBotAvator;