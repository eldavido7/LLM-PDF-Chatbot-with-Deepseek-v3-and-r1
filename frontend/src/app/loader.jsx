import { ClipLoader } from "react-spinners";
import PropTypes from "prop-types";

const Loader = ({
  visible = true,
  size = 20,
  color = "#ffffff",
}) => {
  return (
    <div className="loader-wrapper" style={{ display: visible ? "block" : "none" }}>
      <ClipLoader size={size} color={color} loading={visible} />
    </div>
  );
};

Loader.propTypes = {
  visible: PropTypes.bool,
  size: PropTypes.number,
  color: PropTypes.string,
};

export default Loader;
