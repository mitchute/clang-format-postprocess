namespace EnergyPlus {
    namespace modOneNamespace {

        int modOneInt(0);
        double modOneDouble(0.0);
        std::string modOneString("");

        int const modOneIntConst(0);
        double const modOneDoubleConst(0.0);
        std::string modOneStringConst("");

        int static modOneIntStatic(0);
        double static modOneDoubleStatic(0.0);
        std::string static modOneStringStatic("");

        struct ModOne
        {
            int a;

            ModOne () :
                a(0)
            {}
        };
    }
}
