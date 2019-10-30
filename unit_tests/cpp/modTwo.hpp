namespace EnergyPlus {
    namespace modTwoNamespace {

        int modTwoInt(0);
        double modTwoDouble(0.0);
        std::string modTwoString("");

        int const modTwoIntConst(0);
        double const modTwoDoubleConst(0.0);
        std::string modTwoStringConst("");

        int static modTwoIntStatic(0);
        double static modTwoDoubleStatic(0.0);
        std::string static modTwoStringStatic("");

        struct ModTwo
        {
            int a;

            ModTwo () :
                a(0)
            {}
        };
    }
}
