<div>

    <form role="form" class="addon-settings" method="POST" data-addon="${addon_short_name}">

        <!-- Title -->
        <h4>${addon_full_name}</h4>

        ${self.body()}

            ${self.submit_btn()}

        <!-- Form feedback -->
        <div class="addon-settings-message" style="display: none; padding-top: 10px;"></div>

    </form>

</div>

<%def name="submit_btn()">
    ##<button class="btn btn-success addon-settings-submit">
       ## Submit
    ##</button>
</%def>