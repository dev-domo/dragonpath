import dragonMark from "../assets/character.svg";
import "./AppHeader.css";

export function AppHeader() {
  return (
    <header className="app-header">
      <div className="app-header__brand">
        <img className="app-header__mark" src={dragonMark} alt="DragonPath" />
        <span className="app-header__name">DragonPath</span>
      </div>
    </header>
  );
}
