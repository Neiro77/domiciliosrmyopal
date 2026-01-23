/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      keyframes: {
        fadeInUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        }
      },
      animation: {
        'fade-in-up': 'fadeInUp 0.6s ease-out forwards',
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'pulse-light': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite', // Para indicar actividad
      },
      colors: {
        primary: '#3B82F6', // Un azul principal
        secondary: '#60A5FA', // Un azul más claro
        accent: '#EF4444', // Rojo para acentos o errores
        dark: '#1F2937', // Para textos oscuros
        light: '#F9FAFB', // Para fondos claros
      }
    },
  },
  plugins: [],
}
