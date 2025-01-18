import React from "react";

const Loader: React.FC = () => {
  return (
    <div className="flex justify-center items-center">
      <div id="container" className="flex space-x-2">
        <div id="ball-1" className="circle"></div>
        <div id="ball-2" className="circle"></div>
        <div id="ball-3" className="circle"></div>
      </div>
    </div>
  );
};

export default Loader;
