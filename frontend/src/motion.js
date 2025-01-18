export const slideIn = (direction, delay) => ({
  initial: {
    y: direction === "up" ? 50 : -50,
    opacity: 0,
  },
  animate: {
    y: 0,
    opacity: 1,
    transition: {
      delay: delay * 0.1,
      duration: 0.5,
    },
  },
});

export const fadeIn = (direction, index) => ({
  initial: {
    y: direction === "up" ? 40 : direction === "down" ? -40 : 0,
    x: direction === "left" ? 40 : direction === "right" ? -40 : 0,
    opacity: 0,
    transition: {
      duration: 0.5,
      ease: [0.25, 0.25, 0.25, 0.75],
    },
  },
  animate: {
    y: 0,
    x: 0,
    opacity: 1,
    transition: {
      duration: 0.8,
      delay: index == null ? 1 : index * 0.05,
      ease: [0.5, 0.71, 1, 1.5],
    },
  },
});

export const zoomIn = (index, min) => ({
  initial: {
    scale: min === "min" ? 0.8 : 0,
    opacity: min === "min" ? 0.8 : 0,
    transition: {
      duration: 1,
      ease: [0.25, 0.25, 0.25, 0.75],
    },
  },
  animate: {
    scale: 1,
    opacity: 1,
    transition: {
      duration: 0.8,
      delay: index * 0.05,
      ease: [0.5, 0.71, 1, 1.5],
    },
  },
});

export const fadeStagger = {
  initial: {
    y: -40,
  },
  animate: {
    y: 0,
    transition: {
      duration: 1,
      delay: 0.5,
      delayChildren: 2.4,
      staggerChildren: 0.04,
      staggerDirection: -1,
    },
  },
};
